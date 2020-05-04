import argparse
from argparse import Namespace

OCI = "OCI"
ANSIBLE = "ANSIBLE"
COMPUTE = "COMPUTE"
CLUSTER = "CLUSTER"
NETWORK = "NETWORK"


def strip_argument_prefix(arguments, prefix=""):
    return {k.replace(prefix, ""): v for k, v in arguments.items()}


def _get_arguments(arguments, startswith=""):
    return {k: v for k, v in arguments.items() if k.startswith(startswith)}


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


def add_network_group(parser):
    network_group = parser.add_argument_group(title="Network arguments")
    network_group.add_argument("--network-vcn-id", default=False)
    network_group.add_argument("--network-vcn-name", default=False)
    network_group.add_argument("--network-cidr-block", default="10.0.0.0/16")


def add_cluster_group(parser):
    cluster_group = parser.add_argument_group(title="Cluster arguments")
    cluster_group.add_argument("--cluster-name", default="")
    cluster_group.add_argument("--cluster-kubernetes-version", default=None)


argument_groups = {
    OCI: add_oci_group,
    ANSIBLE: add_ansible_group,
    COMPUTE: add_compute_group,
    CLUSTER: add_cluster_group,
    NETWORK: add_network_group,
}


def get_arguments(argument_types, strip_group_prefix=False):
    parser = argparse.ArgumentParser()

    for argument_group in argument_types:
        if argument_group in argument_groups:
            argument_groups[argument_group](parser)

    args = parser.parse_args()
    if strip_group_prefix:
        stripped_args = {}
        for argument_group in argument_types:
            group_args = _get_arguments(vars(args), argument_group.lower())
            group_args = strip_argument_prefix(group_args, argument_group.lower() + "_")
            stripped_args.update(group_args)
        return Namespace(**stripped_args)
    return args


# def get_arguments():
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--profile-name', default='DEFAULT')
#     parser.add_argument('--compartment-id', default=False)
#     parser.add_argument('--ssh-authorized-keys', nargs='+', default=[])
#     parser.add_argument('--vm-ip', default=False)
#     parser.add_argument('--operating-system', default='CentOS')
#     parser.add_argument('--operating-system-version', default='7')
#     parser.add_argument('--target-shape', default='VM.Standard2.1')
#     return parser.parse_args()


def parse_arguments():
    return parser.parse_args()
