from corc.defaults import PROFILE, INSTANCE
from corc.cli.parsers.providers.ec2.instance import (
    start_instance_group,
    instance_identity_group,
)


def start_instance_groups(parser):
    start_instance_group(parser)

    provider_groups = [PROFILE]
    argument_groups = [INSTANCE]
    return provider_groups, argument_groups


def stop_instance_groups(parser):
    instance_identity_group(parser)

    provider_groups = [PROFILE]
    argument_groups = [INSTANCE]
    return provider_groups, argument_groups


def get_instance_groups(parser):
    instance_identity_group(parser)

    provider_groups = [PROFILE]
    argument_groups = [INSTANCE]
    return provider_groups, argument_groups


def list_instance_groups(parser):
    return [PROFILE], []
