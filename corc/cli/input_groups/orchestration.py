from corc.core.orchestration.defaults import ORCHESTRATION_PROVIDER_NAME
from corc.cli.parsers.orchestration.orchestration import (
    add_provider_group,
    remove_provider_group,
)


def add_provider_groups(parser):
    add_provider_group(parser)

    provider_groups = [ORCHESTRATION_PROVIDER_NAME]
    return provider_groups


def remove_provider_groups(parser):
    remove_provider_group(parser)

    provider_groups = [ORCHESTRATION_PROVIDER_NAME]
    return provider_groups
