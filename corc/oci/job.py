import boto3
import os
import time
from botocore.configloader import load_config
from botocore.credentials import ConfigProvider
from oci.container_engine import (
    ContainerEngineClient,
    ContainerEngineClientCompositeOperations,
)
from kubernetes import client
from kubernetes.client import (
    V1Volume,
    V1SecretVolumeSource,
    V1VolumeMount,
    V1ObjectMeta,
)
from kubernetes.client.rest import ApiException

from corc.defaults import (
    STORAGE_CREDENTIALS_NAME,
    KUBERNETES_NAMESPACE,
    JOB_DEFAULT_NAME,
)
from corc.util import validate_dict_types, validate_dict_values
from corc.storage.staging import required_staging_fields, required_staging_values
from corc.storage.s3 import (
    required_s3_fields,
    required_s3_values,
    bucket_exists,
    upload_to_s3,
    upload_directory_to_s3,
)
from corc.kubernetes.nodes import NodeManager
from corc.kubernetes.scheduler import KubenetesScheduler
from corc.oci.cluster import get_cluster_by_name, refresh_kube_config
from corc.oci.helpers import new_client


def run(
    cluster_kwargs={},
    execute_kwargs={},
    job_kwargs={},
    oci_kwargs={},
    staging_kwargs={},
    storage_kwargs={},
):
    if "name" not in job_kwargs or not job_kwargs["name"]:
        since_epoch = int(time.time())
        job_kwargs["name"] = "{}-{}".format(JOB_DEFAULT_NAME, since_epoch)

    container_engine_client = new_client(
        ContainerEngineClient,
        composite_class=ContainerEngineClientCompositeOperations,
        profile_name=oci_kwargs["profile_name"],
    )

    cluster = get_cluster_by_name(
        container_engine_client,
        oci_kwargs["compartment_id"],
        name=cluster_kwargs["name"],
    )

    if not cluster:
        print("Failed to find a cluster with name: {}".format(cluster_kwargs["name"]))
        return False

    refreshed = refresh_kube_config(cluster.id, profile_name=oci_kwargs["profile_name"])
    if not refreshed:
        exit(1)

    node_manager = NodeManager()
    node_manager.discover()
    node = node_manager.select()

    # Ensure we have the newest config
    scheduler = KubenetesScheduler()

    jobio_args = [
        "jobio",
        "run",
        "--job-name",
        job_kwargs["name"],
        execute_kwargs["command"],
        "--execute-args",
        " ".join(execute_kwargs["args"]),
        "--execute-output-path",
        execute_kwargs["output_path"],
    ]

    if "capture" in execute_kwargs and execute_kwargs["capture"]:
        jobio_args.append("--execute-capture")

    # Maintained by the pod
    volumes = []
    # Maintained by the container
    volume_mounts = []
    # Prepare config for the scheduler
    scheduler_config = {}

    valid_staging_types = validate_dict_types(staging_kwargs, required_staging_fields)
    valid_staging_values = validate_dict_values(staging_kwargs, required_staging_values)
    if valid_staging_types and valid_staging_values:
        # Means that results should be exported to the specified storage
        # Create kubernetes secrets
        core_api = client.CoreV1Api()
        # storage_api = client.StorageV1Api()

        # Storage endpoint credentials secret
        try:
            storage_credentials_secret = core_api.read_namespaced_secret(
                STORAGE_CREDENTIALS_NAME, KUBERNETES_NAMESPACE
            )
        except ApiException as err:
            storage_credentials_secret = None
            print(
                "Failed to find the secret: {}, err: {}".format(
                    STORAGE_CREDENTIALS_NAME, err
                )
            )

        # volumes
        secret_volume_source = V1SecretVolumeSource(
            secret_name=STORAGE_CREDENTIALS_NAME
        )
        secret_volume = V1Volume(
            name=STORAGE_CREDENTIALS_NAME, secret=secret_volume_source
        )
        volumes.append(secret_volume)

        # Where the storage credentials should be mounted
        # in the compute unit
        secret_mount = V1VolumeMount(
            name=STORAGE_CREDENTIALS_NAME,
            mount_path=staging_kwargs["credentials_path"],
            read_only=True,
        )
        volume_mounts.append(secret_mount)

        valid_storage_types = validate_dict_types(storage_kwargs, required_s3_fields)
        valid_storage_values = validate_dict_values(storage_kwargs, required_s3_values)
        # External Storage
        if valid_storage_types and valid_storage_values:
            # S3 storage
            # Look for s3 credentials and config files
            s3_config = load_config(storage_kwargs["config_file"])

            if not s3_config:
                raise RuntimeError(
                    "Failed to load s3 config: {}".format(storage_kwargs["config_file"])
                )

            s3_config_provider = ConfigProvider(
                storage_kwargs["credentials_file"], storage_kwargs["profile_name"]
            )
            s3_creds_config = s3_config_provider.load()
            if not s3_creds_config:
                raise RuntimeError(
                    "Failed to load s3 credentials config: {}".format(
                        storage_kwargs["credentials_file"]
                    )
                )
            (
                s3_access_key,
                s3_secret_key,
                s3_token,
            ) = s3_creds_config.get_frozen_credentials()

            #
            if not storage_credentials_secret:
                secret_data = dict(
                    aws_access_key_id=s3_access_key,
                    aws_secret_access_key=s3_secret_key,
                )
                secret_metadata = V1ObjectMeta(name=STORAGE_CREDENTIALS_NAME)
                secrets_config = dict(metadata=secret_metadata, string_data=secret_data)
                scheduler_config.update(dict(secret_kwargs=secrets_config))

            # If `access_key`
            # TODO, unify argument endpoint, with s3 config endpoint'
            region = s3_config["profiles"][storage_kwargs["profile_name"]][
                "region_name"
            ]
            s3_bucket_config = dict(
                aws_access_key_id=s3_access_key,
                aws_secret_access_key=s3_secret_key,
                region_name=region,
                endpoint_url=staging_kwargs["endpoint"],
            )
            s3 = boto3.resource("s3", **s3_bucket_config)

            if not storage_kwargs["bucket_name"]:
                storage_kwargs["bucket_name"] = job_kwargs["name"]

            bucket = bucket_exists(s3.meta.client, storage_kwargs["bucket_name"])
            if not bucket:
                bucket = s3.create_bucket(
                    Bucket=storage_kwargs["bucket_name"],
                    CreateBucketConfiguration={"LocationConstraint": region},
                )

            if "upload_path" in staging_kwargs and staging_kwargs["upload_path"]:
                # Upload local path to the bucket as designated input for the job
                if os.path.exists(staging_kwargs["upload_path"]):
                    if os.path.isdir(staging_kwargs["upload_path"]):
                        uploaded = upload_directory_to_s3(
                            s3.meta.client,
                            staging_kwargs["upload_path"],
                            storage_kwargs["bucket_name"],
                            s3_prefix=storage_kwargs["bucket_input_prefix"],
                        )
                    elif os.path.isfile(staging_kwargs["upload_path"]):
                        s3_path = os.path.basename(staging_kwargs["upload_path"])
                        if storage_kwargs["bucket_input_prefix"]:
                            s3_path = os.path.join(
                                storage_kwargs["bucket_input_prefix"], s3_path
                            )
                        # Upload
                        uploaded = upload_to_s3(
                            s3.meta.client,
                            staging_kwargs["upload_path"],
                            s3_path,
                            storage_kwargs["bucket_name"],
                        )

                if not uploaded:
                    raise RuntimeError(
                        "Failed to local path: {} in the upload folder to s3".format(
                            staging_kwargs["upload_path"]
                        )
                    )

            jobio_args.extend(
                [
                    "--s3-profile-name",
                    storage_kwargs["profile_name"],
                    "--s3-session-vars",
                    staging_kwargs["credentials_path"],
                    "--s3-bucket-name",
                    storage_kwargs["bucket_name"],
                    "--s3-endpoint-url",
                    staging_kwargs["endpoint"],
                    "--s3-region-name",
                    region,
                    "--s3-input-path",
                    staging_kwargs["input_path"],
                    "--s3-output-path",
                    staging_kwargs["output_path"],
                ]
            )

    if scheduler_config:
        prepared = scheduler.prepare(**scheduler_config)
        if not prepared:
            raise RuntimeError("Failed to prepare the scheduler")

    container_spec = dict(
        name=job_kwargs["name"],
        image=cluster_kwargs["image"],
        args=jobio_args,
        volume_mounts=volume_mounts,
    )
    # args=jobio_args,
    pod_spec = dict(node_name=node.metadata.name, volumes=volumes, dns_policy="Default")
    task = dict(container_kwargs=container_spec, pod_spec_kwargs=pod_spec)

    job_id = scheduler.submit(**task)
    if not job_id:
        exit(1)
