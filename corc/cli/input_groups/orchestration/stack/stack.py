from corc.core.defaults import STACK
from corc.cli.parsers.stack import (
    deploy_group,
    destroy_group,
    show_group,
    ls_group,
)


def deploy_groups(parser):
    deploy_group(parser)

    provider_groups = []
    argument_groups = [STACK]
    return provider_groups, argument_groups


def destroy_groups(parser):
    destroy_group(parser)

    provider_groups = []
    argument_groups = [STACK]
    return provider_groups, argument_groups


def show_groups(parser):
    show_group(parser)

    provider_groups = []
    argument_groups = [STACK]
    return provider_groups, argument_groups


def ls_groups(parser):
    ls_group(parser)

    provider_groups = []
    argument_groups = [STACK]
    return provider_groups, argument_groups
