from corc.core.defaults import PROVIDER
from corc.core.orchestration.defaults import ORCHESTRATION_PROVIDER
from corc.cli.parsers.orchestration.orchestration import (
    add_provider_group,
    remove_provider_group,
)


def add_provider_groups(parser):
    add_provider_group(parser)

    provider_groups = [PROVIDER]
    argument_groups = [ORCHESTRATION_PROVIDER]
    skip_groups = []
    return provider_groups, argument_groups, skip_groups


def remove_provider_groups(parser):
    remove_provider_group(parser)

    provider_groups = [PROVIDER]
    argument_groups = [ORCHESTRATION_PROVIDER]
    skip_groups = []
    return provider_groups, argument_groups, skip_groups
