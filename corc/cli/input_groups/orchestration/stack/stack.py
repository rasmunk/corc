from corc.core.defaults import STACK
from corc.cli.parsers.stack import (
    create_group,
    update_group,
    remove_group,
    deploy_group,
    destroy_group,
    show_group,
    ls_group,
)


def create_groups(parser):
    create_group(parser)

    provider_groups = []
    argument_groups = [STACK]
    return provider_groups, argument_groups


def update_groups(parser):
    update_group(parser)

    provider_groups = []
    argument_groups = [STACK]
    return provider_groups, argument_groups


def remove_groups(parser):
    remove_group(parser)

    provider_groups = []
    argument_groups = [STACK]
    return provider_groups, argument_groups


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
