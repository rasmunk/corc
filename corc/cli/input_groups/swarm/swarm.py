from corc.core.defaults import SWARM
from corc.cli.parsers.swarm import (
    create_group,
    update_group,
    remove_group,
    show_group,
    sync_group,
    ls_group,
)


def create_groups(parser):
    create_group(parser)

    provider_groups = []
    argument_groups = [SWARM]
    return provider_groups, argument_groups


def update_groups(parser):
    update_group(parser)

    provider_groups = []
    argument_groups = [SWARM]
    return provider_groups, argument_groups


def remove_groups(parser):
    remove_group(parser)

    provider_groups = []
    argument_groups = [SWARM]
    return provider_groups, argument_groups


def show_groups(parser):
    show_group(parser)

    provider_groups = []
    argument_groups = [SWARM]
    return provider_groups, argument_groups


def sync_groups(parser):
    sync_group(parser)

    provider_groups = []
    argument_groups = [SWARM]
    return provider_groups, argument_groups


def ls_groups(parser):
    ls_group(parser)

    provider_groups = []
    argument_groups = [SWARM]
    return provider_groups, argument_groups
