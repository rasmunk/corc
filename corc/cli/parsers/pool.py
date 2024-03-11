from corc.core.defaults import POOL, NODE, PACKAGE_NAME
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
        help="The name of the pool that should be removed.",
    )


def show_group(parser):
    pool_group = parser.add_argument_group(title="Pool show arguments")
    pool_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the pool.",
    )


def ls_group(parser):
    pool_group = parser.add_argument_group(title="Pool list arguments")


def add_node_group(parser):
    node_group = parser.add_argument_group(title="Node arguments")
    node_group.add_argument(
        "pool_name",
        action=PositionalArgumentsAction,
        help="The name of the pool that the node should be added to.",
    )
    node_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the node to be added.",
    )
    node_group.add_argument(
        "-s",
        "--state",
        dest="{}_state".format(NODE),
        help="The state of the node.",
    )
    node_group.add_argument(
        "-c",
        "--config",
        dest="{}_config".format(NODE),
        help="The config of the node.",
    )


def remove_node_group(parser):
    node_group = parser.add_argument_group(title="Node arguments")
    node_group.add_argument(
        "pool_name",
        action=PositionalArgumentsAction,
        help="The name of the pool that the node should be removed from.",
    )
    node_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the node.",
    )
