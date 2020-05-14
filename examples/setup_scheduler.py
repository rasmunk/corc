import sys
import os
import boto3
import oci

# Import base
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(base_path, "orchestration"))
sys.path.append(base_path)

from oci.container_engine import (
    ContainerEngineClient,
    ContainerEngineClientCompositeOperations,
)
from kubernetes.client import V1Volume, V1SecretVolumeSource

from cluster import refresh_kube_config, new_client, get_cluster_by_name
from orchestration.kubernetes.scheduler import KubenetesScheduler
from orchestration.kubernetes.job import prepare_job, create_job
from orchestration.kubernetes.nodes import NodeManager
from orchestration.kubernetes.secret import create_secret


here = os.path.dirname(os.path.abspath(__file__))


def upload_directory(client, path, bucket):
    if not os.path.exists(path):
        return False
    for root, dirs, files in os.walk(path):
        for filename in files:
            local_path = os.path.join(root, filename)
            s3_path = os.path.relpath(local_path)
            # Upload
            client.upload_file(local_path, bucket.name, s3_path)
    return True


if __name__ == "__main__":
    profile_name = "XNOVOTECH"
    # Extract OCI cluster id
    container_engine_client = new_client(
        ContainerEngineClient,
        composite_class=ContainerEngineClientCompositeOperations,
        profile_name=profile_name,
    )

    config = oci.config.from_file(profile_name="XNOVOTECH")
    s3_config = dict(
        aws_access_key_id=config["aws_access_key"],
        aws_secret_access_key=config["aws_secret_key"],
        region_name=config["region"],
        endpoint_url="https://axogwpk79um4.compat.objectstorage.eu-amsterdam-1.oraclecloud.com",
    )

    s3 = boto3.resource("s3", **s3_config)

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
    instrument_path = os.path.join(
        os.sep, "usr", "local", "share", "mcxtrace", "examples", instrument_name
    )
    instrument_args = [
        "R=-100",
        "phi_mirror=3",
        "phi_mono=9.25",
        "chi=0",
        "ome=0",
        "phi=0",
        "tth0",
    ]
    output_args = ["-d", os.path.join("tmp", "results")]
    args = ["mxrun", instrument_path]
    args.extend(output_args)
    args.extend(instrument_args)

    job_name = "example-mx-run-container-14"

    # secret_data = dict(
    #     aws_access_key=config["aws_access_key"],
    #     aws_secret_access_key=config["aws_secret_key"],
    # )

    # secrets_config = dict(data=secret_data)

    # config = dict(secret_kwargs=secrets_config)
    # prepared = scheduler.prepare(**config)
    # if not prepared:
    #     return False

    container_spec = dict(args=args, image="nielsbohr/mcstas-mcxtrace", name=job_name)
    pod_spec = dict(node_name=node.metadata.name)
    task = dict(container_kwargs=container_spec, pod_spec_kwargs=pod_spec)

    job_id = scheduler.submit(**task)
    if not job_id:
        exit(1)

    # result = scheduler.retrieve(job_id)
    path = os.path.join(here, "job_files")
    # Bucket name is the job
    bucket = s3.create_bucket(
        Bucket=job_name,
        CreateBucketConfiguration={"LocationConstraint": config["region"]},
    )
    uploaded = upload_directory(s3.meta.client, path, bucket)
    print(uploaded)
