from corc.defaults import ORCHESTRATION
from corc.orchestration.defaults import ORCHESTRATION_PROVIDER
from corc.cli.parsers.orchestration.orchestration import (
    add_provider_group,
    remove_provider_group,
)


def add_provider_groups(parser):
    add_provider_group(parser)

    action_groups = []
    argument_groups = [ORCHESTRATION_PROVIDER]
    return action_groups, argument_groups


def remove_provider_groups(parser):
    remove_provider_group(parser)

    argument_groups = [ORCHESTRATION]
    return [], argument_groups
