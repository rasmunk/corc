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

from corc.core.defaults import STACK, default_persistence_path
from corc.cli.parsers.actions import PositionalArgumentsAction


def valid_create_group(parser):
    create_group(parser)


def valid_update_group(parser):
    update_group(parser)


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
        "-cf",
        "--config-file",
        dest="{}_config".format(STACK),
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
        "id", action=PositionalArgumentsAction, help="The id of the Stack."
    )
    stack_group.add_argument(
        "-n",
        "--name",
        dest="{}_name".format(STACK),
        help="The name of the Stack",
    )
    stack_group.add_argument(
        "-cf",
        "--config-file",
        dest="{}_config".format(STACK),
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
        "id",
        action=PositionalArgumentsAction,
        help="The id of the Stack that should be removed.",
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
        "id",
        action=PositionalArgumentsAction,
        help="The id of the Stack that should be deployed.",
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
        "id",
        action=PositionalArgumentsAction,
        help="The id of the Stack that should be destroyed.",
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
        "id",
        action=PositionalArgumentsAction,
        help="The id of the Stack.",
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
        "-r",
        "--regex",
        dest="{}_regex".format(STACK),
        help="The regex to use when searching for Stacks.",
    )
    stack_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(STACK),
        help="The directory path to where the Stacks should be discovered.",
        default=default_persistence_path,
    )
