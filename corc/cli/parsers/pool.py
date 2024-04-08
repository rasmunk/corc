from corc.core.defaults import INSTANCE
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
    _ = parser.add_argument_group(title="Pool list arguments")


def add_instance_group(parser):
    instance_group = parser.add_argument_group(title="Instance arguments")
    instance_group.add_argument(
        "pool_name",
        action=PositionalArgumentsAction,
        help="The name of the pool that the instance should be added to.",
    )
    instance_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the instance to be added.",
    )
    instance_group.add_argument(
        "-s",
        "--state",
        dest="{}_state".format(INSTANCE),
        help="The state of the instance.",
    )
    instance_group.add_argument(
        "-c",
        "--config",
        dest="{}_config".format(INSTANCE),
        help="The config of the instance.",
    )


def remove_instance_group(parser):
    instance_group = parser.add_argument_group(title="Instance arguments")
    instance_group.add_argument(
        "pool_name",
        action=PositionalArgumentsAction,
        help="The name of the pool that the instance should be removed from.",
    )
    instance_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the instance.",
    )
