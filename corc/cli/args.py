import argparse
from argparse import Namespace
from corc.defaults import (
    ANSIBLE,
    AWS,
    CLUSTER,
    COMPUTE,
    EXECUTE,
    JOB,
    NODE,
    OCI,
    STORAGE,
    SUBNET,
    S3,
    VCN,
)


def strip_argument_prefix(arguments, prefix=""):
    return {k.replace(prefix, ""): v for k, v in arguments.items()}


def _get_arguments(arguments, startswith=""):
    return {k: v for k, v in arguments.items() if k.startswith(startswith)}


def add_oci_group(parser):
    oci_group = parser.add_argument_group(title="OCI arguments")
    oci_group.add_argument("--oci-profile-name", default="DEFAULT")
    oci_group.add_argument("--oci-compartment-id", default="")


def add_aws_group(parser):
    pass
    # aws_group = parser.add_argument_group(title="AWS arguments")


def add_job_meta_group(parser):
    meta_group = parser.add_argument_group(title="Job metadata")
    meta_group.add_argument("--job-name", default=False)
    meta_group.add_argument("--job-debug", action="store_true", default=False)
    meta_group.add_argument("--job-env-override", action="store_true", default=True)
    meta_group.add_argument("--job-num-jobs", default=1, type=int)
    meta_group.add_argument("--job-num-parallel", default=1, type=int)


def add_execute_group(parser):
    execute_group = parser.add_argument_group(title="Execute arguments")
    execute_group.add_argument("execute_command", default="")
    execute_group.add_argument("--execute-args", nargs="*", default="")
    execute_group.add_argument("--execute-capture", action="store_true", default=True)
    execute_group.add_argument("--execute-output-path", default="/tmp/output")


def add_s3_group(parser):
    s3_group = parser.add_argument_group(title="S3 Arguments")
    s3_group.add_argument("--s3-bucket-name", default="")
    s3_group.add_argument("--s3-bucket-input-prefix", default="input")
    s3_group.add_argument("--s3-bucket-output-prefix", default="output")
    s3_group.add_argument("--s3-config-file", default="~/.aws/config")
    s3_group.add_argument("--s3-credentials-file", default="~/.aws/credentials")
    s3_group.add_argument("--s3-profile-name", default="default")


def add_ansible_group(parser):
    ansible_group = parser.add_argument_group(title="Ansible arguments")
    ansible_group.add_argument("--ansible-root-path", default=False)
    ansible_group.add_argument("--ansible-playbook-path", default=False)
    ansible_group.add_argument("--ansible-inventory-path", default=False)


def add_compute_group(parser):
    compute_group = parser.add_argument_group(title="Compute arguments")
    compute_group.add_argument("--compute-ssh-authorized-keys", nargs="+", default=[])
    compute_group.add_argument("--compute-ad", default="", required=True)
    compute_group.add_argument("--compute-os", default="CentOS")
    compute_group.add_argument("--compute-os-version", default="7")
    compute_group.add_argument("--compute-target-shape", default="VM.Standard2.1")


def add_vcn_group(parser):
    vcn_group = parser.add_argument_group(title="VCN arguments")
    vcn_group.add_argument("--vcn-id", default="")
    vcn_group.add_argument("--vcn-dns-label", default=None)
    vcn_group.add_argument("--vcn-display-name", default="VCN Network")
    vcn_group.add_argument("--vcn-cidr-block", default="10.0.0.0/16")


def add_subnet_group(parser):
    subnet_group = parser.add_argument_group(title="Subnet arguments")
    subnet_group.add_argument("--subnet-id", default="")
    subnet_group.add_argument("--subnet-dns-label", default=None)
    subnet_group.add_argument("--subnet-cidr-block", default="10.0.1.0/24")


def valid_cluster_group(parser):
    cluster_group = parser.add_argument_group(title="Cluster arguments")
    cluster_group.add_argument("--cluster-id", default="")
    cluster_group.add_argument("--cluster-name", default="")
    cluster_group.add_argument("--cluster-kubernetes-version", default=None)
    cluster_group.add_argument("--cluster-domain", default="")
    cluster_group.add_argument(
        "--cluster-image", default="nielsbohr/mccode-job-runner:latest"
    )


def start_cluster_group(parser):
    cluster_group = parser.add_argument_group(title="Cluster Start arguments")
    cluster_group.add_argument("--cluster-name", default="", required=True)
    cluster_group.add_argument("--cluster-kubernetes-version", default=None)
    cluster_group.add_argument("--cluster-domain", default="", required=True)


def stop_cluster_group(parser):
    cluster_group = parser.add_argument_group(title="Cluster Stop arguments")
    cluster_group.add_argument("--cluster-id", default="")
    cluster_group.add_argument("--cluster-name", default="")


def run_cluster_job_group(parser):
    cluster_group = parser.add_argument_group(title="Cluster Job arguments")
    cluster = cluster_group.add_mutually_exclusive_group(required=True)
    cluster.add_argument("--cluster-id", default="")
    cluster.add_argument("--cluster-name", default="")
    cluster_group.add_argument(
        "--cluster-image", default="nielsbohr/mccode-job-runner:latest"
    )


def add_node_group(parser):
    node_group = parser.add_argument_group(title="Node arguments")
    node_group.add_argument("--node-availability-domain", default="", required=True)
    node_group.add_argument("--node-name", default="NodePool")
    node_group.add_argument("--node-size", default=1, type=int)
    node_group.add_argument("--node-shape", default="VM.Standard2.1")
    # https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/api/cims/models/oci.cims.models.CreateResourceDetails.html?highlight=availability_domain#oci.cims.models.CreateResourceDetails.availability_domain
    node_group.add_argument("--node-image", default="Oracle-Linux-7.7-2020.03.23-0")


def add_storage_group(parser):
    storage_group = parser.add_argument_group(title="Storage arguments")
    storage_providers = storage_group.add_mutually_exclusive_group()
    storage_providers.add_argument("--storage-s3", action="store_true", default=False)
    storage_group.add_argument("--storage-enable", action="store_true", default=False)
    storage_group.add_argument("--storage-endpoint", default="")
    storage_group.add_argument("--storage-credentials-path", default="/mnt/creds")
    storage_group.add_argument("--storage-upload-path", default="")
    storage_group.add_argument("--storage-input-path", default="/tmp/input")
    storage_group.add_argument("--storage-output-path", default="/tmp/output")


argument_groups = {
    ANSIBLE: add_ansible_group,
    AWS: add_aws_group,
    CLUSTER: valid_cluster_group,
    COMPUTE: add_compute_group,
    EXECUTE: add_execute_group,
    JOB: add_job_meta_group,
    NODE: add_node_group,
    OCI: add_oci_group,
    STORAGE: add_storage_group,
    SUBNET: add_subnet_group,
    S3: add_s3_group,
    VCN: add_vcn_group,
}


def extract_arguments(arguments, argument_types, strip_group_prefix=True):
    if strip_group_prefix:
        stripped_args = {}
        for argument_group in argument_types:
            group_args = _get_arguments(vars(arguments), argument_group.lower())
            group_args = strip_argument_prefix(group_args, argument_group.lower() + "_")
            stripped_args.update(group_args)
        return Namespace(**stripped_args)
    return {}


def get_arguments(argument_types, strip_group_prefix=True, parser=None):
    if not parser:
        parser = argparse.ArgumentParser()

    for argument_group in argument_types:
        if argument_group in argument_groups:
            argument_groups[argument_group](parser)

    args, unknown = parser.parse_known_intermixed_args()
    # args = parser.parse_args()
    if strip_group_prefix:
        stripped_args = {}
        for argument_group in argument_types:
            group_args = _get_arguments(vars(args), argument_group.lower())
            group_args = strip_argument_prefix(group_args, argument_group.lower() + "_")
            stripped_args.update(group_args)
        return Namespace(**stripped_args)
    return args
