from corc.core.defaults import STACK, NODE, PACKAGE_NAME
from corc.cli.parsers.actions import PositionalArgumentsAction


def valid_deploy_group(parser):
    deploy_group(parser)


def valid_destroy_group(parser):
    destroy_group(parser)


def valid_show_group(parser):
    show_group(parser)


def valid_list_group(parser):
    ls_group(parser)


def deploy_group(parser):
    stack_group = parser.add_argument_group(title="Stack create arguments")
    stack_group.add_argument(
        "name", action=PositionalArgumentsAction, help="The name of the stack"
    )
    stack_group.add_argument(
        "deploy_file",
        action=PositionalArgumentsAction,
        help="Which stack file to deploy.",
    )


def destroy_group(parser):
    stack_group = parser.add_argument_group(title="Stack to destroy")
    stack_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the stack that should be removed.",
    )


def show_group(parser):
    stack_group = parser.add_argument_group(title="Stack show arguments")
    stack_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the stack.",
    )


def ls_group(parser):
    stack_group = parser.add_argument_group(title="Stack list arguments")
