import boto3
import os
import time
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

from jobio.storage.s3 import expand_s3_bucket, stage_s3_resource
from corc.defaults import (
    STORAGE_CREDENTIALS_NAME,
    KUBERNETES_NAMESPACE,
    JOB_DEFAULT_NAME,
)
from corc.util import validate_dict_types, validate_dict_values
from corc.storage.staging import (
    required_staging_fields,
    required_staging_values,
    required_get_storage_fields,
    required_get_storage_values,
    required_delete_storage_fields,
    required_delete_storage_values,
)
from corc.storage.s3 import (
    bucket_exists,
    delete_bucket,
    delete_objects,
    list_objects,
    load_s3_config,
    required_s3_fields,
    required_s3_values,
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
        execute_kwargs["command"],
        "--execute-args",
        " ".join(execute_kwargs["args"]),
        "--execute-output-path",
        execute_kwargs["output_path"],
        "--job-name",
        job_kwargs["name"],
    ]

    if "capture" in execute_kwargs and execute_kwargs["capture"]:
        jobio_args.append("--execute-capture")

    if "debug" in execute_kwargs:
        jobio_args.append("--job-debug")

    if "env_override" in job_kwargs:
        jobio_args.append("--job-env-override")

    # Maintained by the pod
    volumes = []
    # Maintained by the container
    volume_mounts = []
    # Environment to pass to the container
    envs = []

    # Prepare config for the scheduler
    scheduler_config = {}

    if staging_kwargs and staging_kwargs["enable"]:
        validate_dict_types(staging_kwargs, required_staging_fields, throw=True)
        validate_dict_values(staging_kwargs, required_staging_values, throw=True)

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

        if storage_kwargs:
            validate_dict_types(storage_kwargs, required_s3_fields, throw=True)
            validate_dict_values(storage_kwargs, required_s3_values, throw=True)
            # S3 storage
            # Look for s3 credentials and config files
            s3_config = load_s3_config(
                storage_kwargs["config_file"],
                storage_kwargs["credentials_file"],
                staging_kwargs["endpoint"],
                profile_name=storage_kwargs["profile_name"],
            )

            if not storage_credentials_secret:
                secret_data = dict(
                    aws_access_key_id=s3_config["aws_access_key_id"],
                    aws_secret_access_key=s3_config["aws_secret_access_key"],
                )
                secret_metadata = V1ObjectMeta(name=STORAGE_CREDENTIALS_NAME)
                secrets_config = dict(metadata=secret_metadata, string_data=secret_data)
                scheduler_config.update(dict(secret_kwargs=secrets_config))

            # If `access_key`
            # TODO, unify argument endpoint, with s3 config endpoint'
            s3 = boto3.resource("s3", **s3_config)

            bucket = bucket_exists(s3.meta.client, storage_kwargs["bucket_name"])
            if not bucket:
                bucket = s3.create_bucket(
                    Bucket=storage_kwargs["bucket_name"],
                    CreateBucketConfiguration={
                        "LocationConstraint": s3_config["region_name"]
                    },
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
                    "--s3-region-name",
                    s3_config["region_name"],
                    "--storage-secrets-dir",
                    staging_kwargs["credentials_path"],
                    "--storage-endpoint",
                    staging_kwargs["endpoint"],
                    "--storage-input-path",
                    staging_kwargs["input_path"],
                    "--storage-output-path",
                    staging_kwargs["output_path"],
                    "--bucket-name",
                    storage_kwargs["bucket_name"],
                    "--bucket-input-prefix",
                    storage_kwargs["bucket_input_prefix"],
                    "--bucket-output-prefix",
                    storage_kwargs["bucket_output_prefix"],
                ]
            )

            if "enable" in staging_kwargs:
                jobio_args.append("--storage-enable")

            # Provide a way to allow pod specific output prefixes
            # field_ref = client.V1ObjectFieldSelector(field_path="metadata.name")
            field_ref = client.V1ObjectFieldSelector(field_path="metadata.name")
            env_var_source = client.V1EnvVarSource(field_ref=field_ref)
            # HACK, Set the output prefix in the bucket to the name of the pod
            env_output_prefix = client.V1EnvVar(
                name="JOBIO_BUCKET_OUTPUT_PREFIX", value_from=env_var_source
            )
            envs.append(env_output_prefix)

    if scheduler_config:
        prepared = scheduler.prepare(**scheduler_config)
        if not prepared:
            raise RuntimeError("Failed to prepare the scheduler")

    container_spec = dict(
        name=job_kwargs["name"],
        image=cluster_kwargs["image"],
        env=envs,
        args=jobio_args,
        volume_mounts=volume_mounts,
    )
    # args=jobio_args,
    pod_spec = dict(node_name=node.metadata.name, volumes=volumes, dns_policy="Default")

    job_spec = dict(
        backoff_limit=2,
        parallelism=job_kwargs["num_parallel"],
        completions=job_kwargs["num_jobs"],
    )

    task = dict(
        container_kwargs=container_spec,
        pod_spec_kwargs=pod_spec,
        job_spec_kwargs=job_spec,
    )

    job_id = scheduler.submit(**task)
    if not job_id:
        exit(1)


def get_results(job_kwargs={}, staging_kwargs={}, storage_kwargs={}):

    validate_dict_types(staging_kwargs, required_get_storage_fields, throw=True)
    validate_dict_values(staging_kwargs, required_get_storage_values, throw=True)

    validate_dict_types(storage_kwargs, required_s3_fields, throw=True)
    validate_dict_values(storage_kwargs, required_s3_values, throw=True)

    # S3 storage
    # Look for s3 credentials and config files
    s3_config = load_s3_config(
        storage_kwargs["config_file"],
        storage_kwargs["credentials_file"],
        staging_kwargs["endpoint"],
        profile_name=storage_kwargs["profile_name"],
    )

    # Download results from s3
    s3_resource = stage_s3_resource(**s3_config)

    # Whether to expand all or a single result
    if "result_prefix" in job_kwargs and job_kwargs["result_prefix"]:
        result_prefix = job_kwargs["result_prefix"]
    else:
        # Use all
        result_prefix = ""

    bucket = bucket_exists(s3_resource.meta.client, job_kwargs["name"])
    if not bucket:
        raise RuntimeError(
            "Could not find a bucket with the name: {}".format(job_kwargs["name"])
        )

    expanded = expand_s3_bucket(
        s3_resource,
        job_kwargs["name"],
        staging_kwargs["download_path"],
        s3_prefix=result_prefix,
    )

    if not expanded:
        raise RuntimeError(
            "Failed to expand the target bucket: {}".format(job_kwargs["name"])
        )


def delete_results(job_kwargs={}, staging_kwargs={}, storage_kwargs={}):

    validate_dict_types(staging_kwargs, required_delete_storage_fields, throw=True)
    validate_dict_values(staging_kwargs, required_delete_storage_values, throw=True)

    validate_dict_types(storage_kwargs, required_s3_fields, throw=True)
    validate_dict_values(storage_kwargs, required_s3_values, throw=True)

    # S3 storage
    # Look for s3 credentials and config files
    s3_config = load_s3_config(
        storage_kwargs["config_file"],
        storage_kwargs["credentials_file"],
        staging_kwargs["endpoint"],
        profile_name=storage_kwargs["profile_name"],
    )

    # Download results from s3
    s3_resource = stage_s3_resource(**s3_config)

    # Whether to expand all or a single result
    if "result_prefix" in job_kwargs and job_kwargs["result_prefix"]:
        result_prefix = job_kwargs["result_prefix"]
    else:
        # Use all
        result_prefix = ""

    bucket = bucket_exists(s3_resource.meta.client, job_kwargs["name"])
    if not bucket:
        raise RuntimeError(
            "Could not find a bucket with the name: {}".format(job_kwargs["name"])
        )

    deleted = delete_objects(s3_resource, job_kwargs["name"], s3_prefix=result_prefix)

    if "Errors" in deleted:
        for error in deleted["Errors"]:
            print("Failed to delete: {}".format(error))

    # If the bucket is empty, remove it as well
    results = list_objects(s3_resource, job_kwargs["name"])

    if not results:
        if not delete_bucket(s3_resource.meta.client, job_kwargs["name"]):
            return False
    return True


def list_results(
    job_kwargs={}, staging_kwargs={}, storage_kwargs={}, storage_extra_kwargs={},
):
    # S3 storage
    # Look for s3 credentials and config files
    s3_config = load_s3_config(
        storage_kwargs["config_file"],
        storage_kwargs["credentials_file"],
        staging_kwargs["endpoint"],
        profile_name=storage_kwargs["profile_name"],
    )

    s3_resource = stage_s3_resource(**s3_config)
    response = {}
    results = []
    if "name" in job_kwargs and job_kwargs["name"]:
        bucket = bucket_exists(s3_resource.meta.client, job_kwargs["name"])
        if not bucket:
            raise RuntimeError(
                "Could not find a bucket with the name: {}".format(job_kwargs["name"])
            )
        results = list_objects(s3_resource, job_kwargs["name"], **storage_extra_kwargs)
    else:
        response = s3_resource.meta.client.list_buckets()
        if "Buckets" in response:
            results = response["Buckets"]
    return results
