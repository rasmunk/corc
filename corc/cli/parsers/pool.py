from corc.core.defaults import POOL, PACKAGE_NAME
from corc.cli.parsers.actions import PositionalArgumentsAction


def valid_create_group(parser):
    create_group(parser)


def valid_remove_group(parser):
    remove_group(parser)


def valid_list_group(parser):
    ls_group(parser)


def create_group(parser):
    pool_group = parser.add_argument_group(title="Pool create arguments")
    pool_group.add_argument(
        "name", action=PositionalArgumentsAction, help="The name of the pool"
    )


def remove_group(parser):
    pool_group = parser.add_argument_group(title="Pool remove arguments")
    pool_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the pool to be removed",
    )


def show_group(parser):
    pool_group = parser.add_argument_group(title="Pool show arguments")
    pool_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The id of the pool to be shown",
    )


def ls_group(parser):
    pool_group = parser.add_argument_group(title="Pool list arguments")
