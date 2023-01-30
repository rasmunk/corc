from corc.defaults import PROVIDER, ORCHESTRATION
from corc.cli.parsers.orchestration.orchestration import (
    add_provider_group,
    remove_provider_group,
)


def add_provider_groups(parser):
    add_provider_group(parser)

    provider_groups = [PROVIDER]
    argument_groups = [ORCHESTRATION]
    return provider_groups, argument_groups


def remove_provider_groups(parser):
    remove_provider_group(parser)

    provider_groups = [PROVIDER]
    argument_groups = [ORCHESTRATION]
    return provider_groups, argument_groups
