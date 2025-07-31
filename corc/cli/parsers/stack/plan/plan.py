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

from corc.core.defaults import PLAN, default_persistence_path
from corc.cli.parsers.actions import PositionalArgumentsAction


def valid_apply_group(parser):
    apply_group(parser)


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


def apply_group(parser):
    apply_group = parser.add_argument_group(title="Plan apply arguments")
    apply_group.add_argument(
        "id",
        action=PositionalArgumentsAction,
        help="The id of the Plan that should be applied.",
    )


def create_group(parser):
    plan_group = parser.add_argument_group(title="Plan create arguments")
    plan_group.add_argument(
        "name", action=PositionalArgumentsAction, help="The name of the Plan"
    )
    plan_group.add_argument(
        "-cf",
        "--config-file",
        dest="{}_config".format(PLAN),
        help="The path to a file that contains a Plan configuration that should be associated with the Plan that is created.",
    )
    plan_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(PLAN),
        help="The directory path to where the Plan database should be located/created.",
        default=default_persistence_path,
    )


def update_group(parser):
    plan_group = parser.add_argument_group(title="Plan update arguments")
    plan_group.add_argument(
        "name", action=PositionalArgumentsAction, help="The name of the Plan."
    )
    plan_group.add_argument(
        "-cf",
        "--config-file",
        dest="{}_config".format(PLAN),
        help="The path to a file that contains a Plan configuration that should be used to update the Plan with.",
    )
    plan_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(PLAN),
        help="The directory path to where the Plan database is located.",
        default=default_persistence_path,
    )


def remove_group(parser):
    plan_group = parser.add_argument_group(title="Plan remove arguments")
    plan_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the Plan that should be removed.",
    )
    plan_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(PLAN),
        help="The directory path to where the Plan database is located.",
        default=default_persistence_path,
    )


def deploy_group(parser):
    plan_group = parser.add_argument_group(title="Plan deploy arguments")
    plan_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the Plan that should be deployed.",
    )
    plan_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(PLAN),
        help="The directory path to where the Plan should be created.",
        default=default_persistence_path,
    )


def destroy_group(parser):
    plan_group = parser.add_argument_group(title="Plan to destroy")
    plan_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the Plan that should be destroyed.",
    )
    plan_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(PLAN),
        help="The directory path to where the Plan should be destroyed.",
        default=default_persistence_path,
    )


def show_group(parser):
    plan_group = parser.add_argument_group(title="Plan show arguments")
    plan_group.add_argument(
        "name",
        action=PositionalArgumentsAction,
        help="The name of the Plan.",
    )
    plan_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(PLAN),
        help="The directory path to where the Plan should be found.",
        default=default_persistence_path,
    )


def ls_group(parser):
    plan_group = parser.add_argument_group(title="Plan list arguments")
    plan_group.add_argument(
        "-d",
        "--directory",
        dest="{}_directory".format(PLAN),
        help="The directory path to where the Stacks should be discovered.",
        default=default_persistence_path,
    )
