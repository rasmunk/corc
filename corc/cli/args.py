import argparse
from argparse import Namespace
from corc.defaults import (
    ANSIBLE,
    CLUSTER,
    CONFIG,
    INSTANCE,
    JOB,
    OCI,
    STORAGE,
    STORAGE_S3,
    VCN,
)
from corc.cli.configurer.ansible import valid_ansible_group
from corc.cli.parsers.cluster.cluster import valid_cluster_group
from corc.cli.parsers.config.config import valid_config_group
from corc.cli.parsers.instance.instance import valid_instance_group
from corc.cli.parsers.job.job import valid_job_group
from corc.cli.parsers.network.vcn import valid_vcn_group
from corc.cli.parsers.providers.oci.profile import valid_oci_group
from corc.cli.parsers.storage.storage import valid_storage_group
from corc.cli.parsers.storage.s3 import valid_s3_group


def strip_argument_prefix(arguments, prefix=""):
    return {k.replace(prefix, ""): v for k, v in arguments.items()}


def _get_arguments(arguments, startswith=""):
    return {k: v for k, v in arguments.items() if k.startswith(startswith)}


argument_groups = {
    ANSIBLE: valid_ansible_group,
    CLUSTER: valid_cluster_group,
    INSTANCE: valid_instance_group,
    CONFIG: valid_config_group,
    JOB: valid_job_group,
    OCI: valid_oci_group,
    STORAGE: valid_storage_group,
    STORAGE_S3: valid_s3_group,
    VCN: valid_vcn_group,
}


def extract_arguments(arguments, argument_types, strip_group_prefix=True):
    stripped_args = {}
    for argument_group in argument_types:
        arguments_dict = vars(arguments)
        group_args = _get_arguments(arguments_dict, argument_group.lower())
        if strip_group_prefix:
            group_args = strip_argument_prefix(group_args, argument_group.lower() + "_")
        stripped_args.update(group_args)
    return Namespace(**stripped_args)


def wrap_extract_arguments(arguments, argument_types, strip_group_prefix=True):
    wrapped_arguments = {}
    for argument_group in argument_types:
        lower_argument_group = argument_group.lower()
        arguments_dict = vars(arguments)
        group_args = _get_arguments(arguments_dict, lower_argument_group)
        if strip_group_prefix:
            group_args = strip_argument_prefix(group_args, lower_argument_group + "_")
        wrapped_arguments[lower_argument_group] = group_args
    return wrapped_arguments


def get_arguments(argument_types, strip_group_prefix=True, parser=None):
    if not parser:
        parser = argparse.ArgumentParser()

    for argument_group in argument_types:
        if argument_group in argument_groups:
            argument_groups[argument_group](parser)

    args, unknown = parser.parse_known_intermixed_args()
    if strip_group_prefix:
        stripped_args = {}
        for argument_group in argument_types:
            group_args = _get_arguments(vars(args), argument_group.lower())
            group_args = strip_argument_prefix(group_args, argument_group.lower() + "_")
            stripped_args.update(group_args)
        return Namespace(**stripped_args)
    return args
