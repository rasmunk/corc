from corc.core.defaults import SWARM
from corc.core.swarm.defaults import default_swarm_perstistence_path
from corc.cli.parsers.actions import PositionalArgumentsAction


def valid_create_group(parser):
    create_group(parser)


def valid_update_group(parser):
    update_group(parser)


def valid_remove_group(parser):
    remove_group(parser)


def valid_show_group(parser):
    show_group(parser)


def valid_sync_group(parser):
    sync_group(parser)


def valid_list_group(parser):
    ls_group(parser)


def create_group(parser):
    swarm_group = parser.add_argument_group(title="Swarm create arguments")
    swarm_group.add_argument(
        "name", action=PositionalArgumentsAction, help="The name of the Swarm"
    )
    swarm_group.add_argument(
        "-cf",
        "--config-file",
        dest="{}_config_file".format(SWARM),
        help="The path to a file that contains a Swarm configuration that should be associated with the Swarm that is created.",
    )
    swarm_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(SWARM),
        help="The directory path to where the Swarm database should be located/created.",
        default=default_swarm_perstistence_path,
    )


def update_group(parser):
    swarm_group = parser.add_argument_group(title="Swarm update arguments")
    swarm_group.add_argument(
        "name", action=PositionalArgumentsAction, help="The name of the Swarm."
    )
    swarm_group.add_argument(
        "-cf",
        "--config-file",
        dest="{}_config_file".format(SWARM),
        help="The path to a file that contains a Swarm configuration that should be used to update the Swarm with.",
    )
    swarm_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(SWARM),
        help="The directory path to where the Swarm database is located.",
        default=default_swarm_perstistence_path,
    )


def remove_group(parser):
    swarm_group = parser.add_argument_group(title="Swarm remove arguments")
    swarm_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the Swarm that should be removed.",
    )
    swarm_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(SWARM),
        help="The directory path to where the Swarm database is located.",
        default=default_swarm_perstistence_path,
    )


def show_group(parser):
    swarm_group = parser.add_argument_group(title="Swarm show arguments")
    swarm_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the Swarm.",
    )
    swarm_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(SWARM),
        help="The directory path to where the Swarm should be found.",
        default=default_swarm_perstistence_path,
    )


def sync_group(parser):
    swarm_group = parser.add_argument_group(title="Swarm sync arguments")
    swarm_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the Swarm.",
    )
    swarm_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(SWARM),
        help="The directory path to where the Swarm should be found.",
        default=default_swarm_perstistence_path,
    )


def ls_group(parser):
    swarm_group = parser.add_argument_group(title="Swarm list arguments")
    swarm_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(SWARM),
        help="The directory path to where the Swarms should be discovered.",
        default=default_swarm_perstistence_path,
    )
