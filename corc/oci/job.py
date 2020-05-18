from botocore.configloader import load_config
from botocore.credentials import ConfigProvider
import oci
import time

from oci.container_engine import (
    ContainerEngineClient,
    ContainerEngineClientCompositeOperations,
)

from corc.defaults import STORAGE_CREDENTIALS_SECRET, KUBERNETES_NAMESPACE
from corc.kubernetes.nodes import NodeManager
from corc.kubernetes.scheduler import KubenetesScheduler
from corc.oci.cluster import get_cluster_by_name, refresh_kube_config, list_entities
from corc.oci.helpers import new_client


def run(
    cluster_kwargs={},
    execute_kwargs={},
    job_kwargs={},
    oci_kwargs={},
    storage_kwargs={},
):
    if "name" not in job_kwargs:
        since_epoch = int(time.time())
        job_kwargs["name"] = "job-{}".format(since_epoch)

    container_engine_client = new_client(
        ContainerEngineClient,
        composite_class=ContainerEngineClientCompositeOperations,
        profile_name=oci_kwargs["profile_name"],
    )

    config = oci.config.from_file(profile_name=oci_kwargs["profile_name"])
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

    # Maintained by the pod
    volumes = []
    # Maintained by the container
    volume_mounts = []

    storage_provider = None
    if storage_kwargs:

        # Required keys, `mount_path`, `endpoint`
        if 'mount_path' not in storage_kwargs:
            raise RuntimeError("Missing required argument `mount_path`")

        if 'endpoint' not in storage_kwargs:
            raise RuntimeError("Missing required argument `endpoint`")

        # Means that results should be exported to the specified storage

        # Create kubernetes secrets
        core_api = client.CoreV1Api()
        storage_api = client.StorageV1Api()

        # Shared secret that contains the storage credentials
        try:
            existing_secret = core_api.read_namespaced_secret(
                STORAGE_CREDENTIALS_SECRET, KUBERNETES_NAMESPACE
            )
        except ApiException as err:
            existing_secret = None
            print(
                "Failed to find the secret: {}, err: {}".format(
                    STORAGE_CREDENTIALS_SECRET, err
                )
            )

        # volumes
        # volume_name = "aws-credentials-mount"
        volume_name = STORAGE_CREDENTIALS_SECRET
        secret_volume_source = V1SecretVolumeSource(secret_name=aws_secret_name)
        secret_volume = V1Volume(name=volume_name, secret=secret_volume_source)
        volumes.append(secret_volume)

    #     mount_path = os.path.join(os.sep, "mnt", "aws", "credentials")
        secret_mount = V1VolumeMount(
            name=volume_name, mount_path=storage_kwargs['mount_path'], read_only=True
        )
        volume_mounts.append(secret_mount)

        # External Storage
        if 's3' in storage_kwargs:
            # S3 storage
            s3_credentials_config = None
            # Look for s3 credentials and config files
            if 'config_file' in storage_kwargs:
                s3_config = load_config(storage_kwargs['credentials_file'])
                
            if 'credentials_file' in storage_kwargs:
                config_provider = ConfigProvider(storage_kwargs['credentials_file']
                                                 oci_kwargs['profile_name'])
                creds = config_provider.load()
                if not creds:
                    raise RuntimeError("Failed to load s3 credentials")
                access_key, secret_key = creds.get_frozen_credentials()

        # If `access_key`, 

    #     s3_config = dict(
    #         aws_access_key_id=config["aws_access_key"],
    #         aws_secret_access_key=config["aws_secret_key"],
    #         region_name=config["region"],
    #         endpoint_url=config["aws_endpoint_url"],
    #     )
    #     # Upload instrument files to the storage bucket
    #     s3 = boto3.resource("s3", **s3_config)
    #     bucket = bucket_exists(s3.meta.client, job_kwargs["name"])
    #     if not bucket:
    #         bucket = s3.create_bucket(
    #             Bucket=job_kwargs["name"],
    #             CreateBucketConfiguration={"LocationConstraint": config["region"]},
    #         )

    #     if s3_args.input_path:
    #         uploaded = upload_to_s3(
    #             s3.meta.client,
    #             s3_args.input_path,
    #             os.path.join(s3_args.bucket_input_prefix, instrument_name),
    #             job_kwargs["name"],
    #         )
    #         if not uploaded:
    #             print("Failed to upload: {}".format(uploaded))
    #             exit(1)

    job_io_args = [
        "job_io",
        "--job-name",
        job_kwargs["name"],
        "--job-command",
        execute_kwargs["command"],
        "--job-args",
        execute_kwargs["args"],
    ]

    print(job_io_args)
    container_spec = dict(
        name=job_kwargs["name"],
        image=cluster_kwargs["image"],
        args=job_io_args,
        volume_mounts=volume_mounts,
    )
    # args=job_io_args,
    pod_spec = dict(node_name=node.metadata.name, volumes=volumes, dns_policy="Default")
    task = dict(container_kwargs=container_spec, pod_spec_kwargs=pod_spec)

    job_id = scheduler.submit(**task)
    if not job_id:
        exit(1)
