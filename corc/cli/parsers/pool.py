# Copyright (C) 2024  rasmunk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from corc.core.defaults import INSTANCE, POOL, default_persistence_path
from corc.cli.parsers.actions import PositionalArgumentsAction


def valid_create_group(parser):
    create_group(parser)


def valid_remove_group(parser):
    remove_group(parser)


def valid_show_group(parser):
    show_group(parser)


def valid_list_group(parser):
    ls_group(parser)


def create_group(parser):
    pool_group = parser.add_argument_group(title="Pool create arguments")
    pool_group.add_argument(
        "name", action=PositionalArgumentsAction, help="The name of the pool"
    )
    pool_group.add_argument(
        "-cf",
        "--config-file",
        dest="{}_config_file".format(POOL),
        help="The path to a file that contains a Pool configuration.",
    )
    pool_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(POOL),
        help="The directory path to where the pool should be created.",
        default=default_persistence_path,
    )


def remove_group(parser):
    pool_group = parser.add_argument_group(title="Pool remove arguments")
    pool_group.add_argument(
        "id",
        action=PositionalArgumentsAction,
        help="The id of the pool that should be removed.",
    )
    pool_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(POOL),
        help="The directory path to where the pool is located.",
        default=default_persistence_path,
    )


def show_group(parser):
    pool_group = parser.add_argument_group(title="Pool show arguments")
    pool_group.add_argument(
        "id",
        action=PositionalArgumentsAction,
        help="The id of the pool.",
    )
    pool_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(POOL),
        help="The directory path to where the pool is located.",
        default=default_persistence_path,
    )


def ls_group(parser):
    pool_group = parser.add_argument_group(title="Pool list arguments")
    pool_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(POOL),
        help="The directory path to where the pools are located.",
        default=default_persistence_path,
    )


def add_instance_group(parser):
    instance_group = parser.add_argument_group(title="Instance arguments")
    instance_group.add_argument(
        "id",
        action=PositionalArgumentsAction,
        help="The id of the pool that the instance should be added to.",
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
    instance_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(INSTANCE),
        help="The directory path to where the pool is located.",
        default=default_persistence_path,
    )


def remove_instance_group(parser):
    instance_group = parser.add_argument_group(title="Instance arguments")
    instance_group.add_argument(
        "id",
        action=PositionalArgumentsAction,
        help="The id of the pool that the instance should be removed from.",
    )
    instance_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the instance.",
    )
    instance_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(INSTANCE),
        help="The directory path to where the pool is located.",
        default=default_persistence_path,
    )
