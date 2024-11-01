from corc.core.defaults import STACK, default_persistence_path
from corc.cli.parsers.actions import PositionalArgumentsAction


def valid_create_group(parser):
    create_group(parser)


def valid_remove_group(parser):
    remove_group(parser)


def valid_deploy_group(parser):
    deploy_group(parser)


def valid_destroy_group(parser):
    destroy_group(parser)


def valid_show_group(parser):
    show_group(parser)


def valid_list_group(parser):
    ls_group(parser)


def create_group(parser):
    stack_group = parser.add_argument_group(title="Stack create arguments")
    stack_group.add_argument(
        "name", action=PositionalArgumentsAction, help="The name of the Stack"
    )
    stack_group.add_argument(
        "-df",
        "--config-file",
        dest="{}_config_file".format(STACK),
        help="The path to a file that contains a Stack configuration that should be associated with the Stack that is created.",
    )
    stack_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(STACK),
        help="The directory path to where the Stack database should be located/created.",
        default=default_persistence_path,
    )


def update_group(parser):
    stack_group = parser.add_argument_group(title="Stack update arguments")
    stack_group.add_argument(
        "name", action=PositionalArgumentsAction, help="The name of the Stack."
    )
    stack_group.add_argument(
        "-df",
        "--config-file",
        dest="{}_config_file".format(STACK),
        help="The path to a file that contains a Stack configuration that should be used to update the Stack with.",
    )
    stack_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(STACK),
        help="The directory path to where the Stack database is located.",
        default=default_persistence_path,
    )


def remove_group(parser):
    stack_group = parser.add_argument_group(title="Stack remove arguments")
    stack_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the Stack that should be removed.",
    )
    stack_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(STACK),
        help="The directory path to where the Stack database is located.",
        default=default_persistence_path,
    )


def deploy_group(parser):
    stack_group = parser.add_argument_group(title="Stack deploy arguments")
    stack_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the Stack that should be deployed.",
    )
    stack_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(STACK),
        help="The directory path to where the Stack should be created.",
        default=default_persistence_path,
    )


def destroy_group(parser):
    stack_group = parser.add_argument_group(title="Stack to destroy")
    stack_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the Stack that should be destroyed.",
    )
    stack_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(STACK),
        help="The directory path to where the Stack should be destroyed.",
        default=default_persistence_path,
    )


def show_group(parser):
    stack_group = parser.add_argument_group(title="Stack show arguments")
    stack_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the Stack.",
    )
    stack_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(STACK),
        help="The directory path to where the Stack should be found.",
        default=default_persistence_path,
    )


def ls_group(parser):
    stack_group = parser.add_argument_group(title="Stack list arguments")
    stack_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(STACK),
        help="The directory path to where the Stacks should be discovered.",
        default=default_persistence_path,
    )
