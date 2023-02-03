from corc.core.defaults import PROVIDER, CONFIGURER
from corc.cli.parsers.configurer.configurer import (
    add_provider_group,
    remove_provider_group,
)


def add_provider_groups(parser):
    add_provider_group(parser)

    provider_groups = [PROVIDER]
    argument_groups = [CONFIGURER]
    skip_groups = []
    return provider_groups, argument_groups, skip_groups


def remove_provider_groups(parser):
    remove_provider_group(parser)

    provider_groups = [PROVIDER]
    argument_groups = [CONFIGURER]
    skip_groups = []
    return provider_groups, argument_groups, skip_groups
