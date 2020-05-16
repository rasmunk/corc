import sys
import os
import boto3
import botocore
import oci
import time

# Import base
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(base_path, "orchestration"))
sys.path.append(base_path)

from oci.container_engine import (
    ContainerEngineClient,
    ContainerEngineClientCompositeOperations,
)
from kubernetes import client
from kubernetes.client import (
    V1Volume,
    V1SecretVolumeSource,
    V1ObjectMeta,
    V1VolumeMount,
)
from kubernetes.client.rest import ApiException
from cluster import refresh_kube_config, new_client, get_cluster_by_name
from orchestration.kubernetes.scheduler import KubenetesScheduler
from orchestration.kubernetes.nodes import NodeManager
from orchestration.args import get_arguments, S3


here = os.path.dirname(os.path.abspath(__file__))


def upload_to_s3(s3_client, local_path, s3_path, bucket_name):
    if not os.path.exists(local_path):
        return False
    s3_client.upload_file(local_path, bucket_name, s3_path)
    return True


def upload_directory(client, path, bucket, s3_prefix="input"):
    if not os.path.exists(path):
        return False
    for root, dirs, files in os.walk(path):
        for filename in files:
            local_path = os.path.join(root, filename)
            # generate s3 dir path
            # Skip the first /
            # HACK
            s3_path = local_path.split(path)[1][1:]
            # Upload
            if s3_prefix:
                s3_path = os.path.join(s3_prefix, s3_path)
            client.upload_file(local_path, bucket.name, s3_path)
    return True


def bucket_exists(s3_client, bucket_name):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return True
    except botocore.exceptions.ClientError:
        pass
    return False


if __name__ == "__main__":
    s3_args = get_arguments([S3], strip_group_prefix=True)
    profile_name = "XNOVOTECH"
    # Extract OCI cluster id
    container_engine_client = new_client(
        ContainerEngineClient,
        composite_class=ContainerEngineClientCompositeOperations,
        profile_name=profile_name,
    )

    config = oci.config.from_file(profile_name="XNOVOTECH")
    compartment_id = "ocid1.tenancy.oc1..aaaaaaaakfmksyrf7hl2gfexmjpb6pbyrirm6k3ro7wd464y2pr7atpxpv4q"
    cluster_name = "Test XNOVOTECH Cluster"
    cluster = get_cluster_by_name(
        container_engine_client, compartment_id, name=cluster_name
    )

    refreshed = refresh_kube_config(cluster.id, profile_name=profile_name)
    if not refreshed:
        exit(1)

    node_manager = NodeManager()
    node_manager.discover()
    node = node_manager.select()

    # Ensure we have the newest config
    scheduler = KubenetesScheduler()

    instrument_name = "MAXII_711.instr"
    instrument_args = [
        "R=-100",
        "phi_mirror=3",
        "phi_mono=9.25",
        "chi=0",
        "ome=0",
        "phi=0",
        "tth0",
    ]
    input_args = os.path.join(os.sep, "tmp", "input", instrument_name)
    output_args = ["-d", os.path.join(os.sep, "tmp", "output")]
    job_args = [input_args]
    job_args.extend(output_args)
    job_args.extend(instrument_args)

    # Create kubernetes secrets
    core_api = client.CoreV1Api()
    storage_api = client.StorageV1Api()
    aws_secret_name = "settings.aws.xnovotech"
    schedule_config = {}
    kubernetes_namespace = "default"
    try:
        existing_secret = core_api.read_namespaced_secret(
            aws_secret_name, kubernetes_namespace
        )
    except ApiException as err:
        existing_secret = None
        print("Failed to find the secret, err: {}".format(err))

    s3_config = dict(
        aws_access_key_id=config["aws_access_key"],
        aws_secret_access_key=config["aws_secret_key"],
        region_name=config["region"],
        endpoint_url=config["aws_endpoint_url"],
    )

    if not existing_secret:
        secret_data = dict(
            aws_access_key_id=config["aws_access_key"],
            aws_secret_access_key=config["aws_secret_key"],
        )
        secret_metadata = V1ObjectMeta(name=aws_secret_name)
        secrets_config = dict(metadata=secret_metadata, string_data=secret_data)
        schedule_config.update(dict(secret_kwargs=secrets_config))

    if schedule_config:
        prepared = scheduler.prepare(**schedule_config)
        if not prepared:
            exit(1)

    # volumes
    volumes = []
    volume_name = "aws-credentials-mount"
    secret_volume_source = V1SecretVolumeSource(secret_name=aws_secret_name)
    secret_volume = V1Volume(name=volume_name, secret=secret_volume_source)
    volumes.append(secret_volume)

    volume_mounts = []
    mount_path = os.path.join(os.sep, "mnt", "aws", "credentials")
    secret_mount = V1VolumeMount(
        name=volume_name, mount_path=mount_path, read_only=True
    )
    volume_mounts.append(secret_mount)
    since_epoch = int(time.time())
    job_name = "example-mx-run-container-{}".format(since_epoch)
    s3_endpoint = (
        "https://axogwpk79um4.compat.objectstorage.eu-amsterdam-1.oraclecloud.com"
    )

    # Upload instrument files to the storage bucket
    s3 = boto3.resource("s3", **s3_config)
    bucket = bucket_exists(s3.meta.client, job_name)
    if not bucket:
        bucket = s3.create_bucket(
            Bucket=job_name,
            CreateBucketConfiguration={"LocationConstraint": config["region"]},
        )

    if s3_args.input_path:
        uploaded = upload_to_s3(
            s3.meta.client,
            s3_args.input_path,
            os.path.join(s3_args.bucket_input_prefix, instrument_name),
            job_name,
        )
        if not uploaded:
            print("Failed to upload: {}".format(uploaded))
            exit(1)

    job_io_args = [
        "job_io",
        "--job-name",
        job_name,
        "--s3-bucket-name",
        job_name,
        "--s3-session-vars",
        mount_path,
        "--s3-endpoint-url",
        s3_endpoint,
        "--s3-region-name",
        config["region"],
        "--job-command",
        "mxrun",
        "--job-args",
        " ".join(job_args),
    ]

    print(job_io_args)
    container_spec = dict(
        name=job_name,
        image="nielsbohr/mccode-job-runner:latest",
        args=job_io_args,
        volume_mounts=volume_mounts,
    )
    # args=job_io_args,
    pod_spec = dict(node_name=node.metadata.name, volumes=volumes, dns_policy="Default")
    task = dict(container_kwargs=container_spec, pod_spec_kwargs=pod_spec)

    job_id = scheduler.submit(**task)
    if not job_id:
        exit(1)

    # Retrieve results

    # result = scheduler.retrieve(job_id)
