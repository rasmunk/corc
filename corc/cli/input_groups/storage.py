from corc.core.defaults import PROVIDER, STORAGE
from corc.cli.parsers.storage.storage import (
    add_provider_group,
    remove_provider_group,
)


def add_provider_groups(parser):
    add_provider_group(parser)

    provider_groups = [PROVIDER]
    argument_groups = [STORAGE]
    skip_groups = []
    return provider_groups, argument_groups, skip_groups


def remove_provider_groups(parser):
    remove_provider_group(parser)

    provider_groups = [PROVIDER]
    argument_groups = [STORAGE]
    skip_groups = []
    return provider_groups, argument_groups, skip_groups
