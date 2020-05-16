import argparse
from argparse import Namespace

OCI = "OCI"
ANSIBLE = "ANSIBLE"
COMPUTE = "COMPUTE"
CLUSTER = "CLUSTER"
NODE = "NODE"
VCN = "VCN"
SUBNET = "SUBNET"
JOB = "JOB"
S3 = "S3"


def strip_argument_prefix(arguments, prefix=""):
    return {k.replace(prefix, ""): v for k, v in arguments.items()}


def _get_arguments(arguments, startswith=""):
    return {k: v for k, v in arguments.items() if k.startswith(startswith)}


def add_job_group(parser):
    job_group = parser.add_argument_group(title="JOB arguments")
    job_group.add_argument("--job-name", default="DEFAULT")
    job_group.add_argument("--job-command", default="")
    job_group.add_argument("--job-args", nargs="*", default="")
    job_group.add_argument("--job-verbose-output", default=True)
    job_group.add_argument("--job-s3-upload-path", default=False)


def add_s3_group(parser):
    s3_group = parser.add_argument_group(title="S3 arguments")
    s3_group.add_argument("--s3-credentials", default="~/.aws/credentials")
    s3_group.add_argument("--s3-config", default="~/.aws/config")
    s3_group.add_argument("--s3-endpoint-url", default=False)
    s3_group.add_argument("--s3-bucket-name", default=False)
    s3_group.add_argument("--s3-input-path", default=False)
    s3_group.add_argument("--s3-bucket-input-prefix", default="input")
    s3_group.add_argument("--s3-output-path", default="/tmp/output")
    s3_group.add_argument("--s3-bucket-output-prefix", default="output")


def add_oci_group(parser):
    oci_group = parser.add_argument_group(title="OCI arguments")
    oci_group.add_argument("--oci-profile-name", default="DEFAULT")
    oci_group.add_argument("--oci-compartment-id", default=False)


def add_ansible_group(parser):
    ansible_group = parser.add_argument_group(title="Ansible arguments")
    ansible_group.add_argument("--ansible-root-path", default=False)
    ansible_group.add_argument("--ansible-playbook-path", default=False)
    ansible_group.add_argument("--ansible-inventory-path", default=False)


def add_compute_group(parser):
    compute_group = parser.add_argument_group(title="Compute arguments")
    compute_group.add_argument("--compute-ssh-authorized-keys", nargs="+", default=[])
    compute_group.add_argument("--compute-operating-system", default="CentOS")
    compute_group.add_argument("--compute-operating-system-version", default="7")
    compute_group.add_argument("--compute-target-shape", default="VM.Standard2.1")


def add_vcn_group(parser):
    vcn_group = parser.add_argument_group(title="VCN arguments")
    vcn_group.add_argument("--vcn-id", default=None)
    vcn_group.add_argument("--vcn-dns-label", default=None)
    vcn_group.add_argument("--vcn-display-name", default=None)
    vcn_group.add_argument("--vcn-cidr-block", default="10.0.0.0/16")


def add_subnet_group(parser):
    subnet_group = parser.add_argument_group(title="Subnet arguments")
    subnet_group.add_argument("--subnet-id", default=None)
    subnet_group.add_argument("--subnet-dns-label", default=None)
    subnet_group.add_argument("--subnet-cidr-block", default="10.0.1.0/24")


def add_cluster_group(parser):
    cluster_group = parser.add_argument_group(title="Cluster arguments")
    cluster_group.add_argument("--cluster-name", default="")
    cluster_group.add_argument("--cluster-kubernetes-version", default=None)


def add_node_group(parser):
    node_group = parser.add_argument_group(title="Node arguments")
    node_group.add_argument(
        "--node-availability-domain", default="Xfze:eu-amsterdam-1-AD-1"
    )
    node_group.add_argument("--node-name", default=False)
    node_group.add_argument("--node-size", default=1, type=int)
    node_group.add_argument("--node-shape", default="VM.Standard2.1")
    # https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/api/cims/models/oci.cims.models.CreateResourceDetails.html?highlight=availability_domain#oci.cims.models.CreateResourceDetails.availability_domain
    node_group.add_argument("--node-image-name", default="Oracle-Linux-7.7")


argument_groups = {
    OCI: add_oci_group,
    ANSIBLE: add_ansible_group,
    COMPUTE: add_compute_group,
    CLUSTER: add_cluster_group,
    NODE: add_node_group,
    VCN: add_vcn_group,
    SUBNET: add_subnet_group,
    JOB: add_job_group,
    S3: add_s3_group,
}


def get_arguments(argument_types, strip_group_prefix=False):
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
