from corc.core.defaults import POOL
from corc.cli.parsers.pool import (
    create_group,
    remove_group,
    show_group,
    ls_group,
    add_instance_group,
    remove_instance_group,
)


def create_groups(parser):
    create_group(parser)

    provider_groups = []
    argument_groups = [POOL]
    return provider_groups, argument_groups


def remove_groups(parser):
    remove_group(parser)

    provider_groups = []
    argument_groups = [POOL]
    return provider_groups, argument_groups


def show_groups(parser):
    show_group(parser)

    provider_groups = []
    argument_groups = [POOL]
    return provider_groups, argument_groups


def ls_groups(parser):
    ls_group(parser)

    provider_groups = []
    argument_groups = [POOL]
    return provider_groups, argument_groups


def add_instance_groups(parser):
    add_instance_group(parser)

    provider_groups = []
    argument_groups = [POOL]
    return provider_groups, argument_groups


def remove_instance_groups(parser):
    remove_instance_group(parser)

    provider_groups = []
    argument_groups = [POOL]
    return provider_groups, argument_groups
