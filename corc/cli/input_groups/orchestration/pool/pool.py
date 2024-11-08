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

from corc.core.defaults import POOL, INSTANCE
from corc.cli.parsers.pool import (
    create_group,
    remove_group,
    show_group,
    ls_group,
    add_instance_group,
    remove_instance_group,
)


def create_groups(parser):
    create_group(parser)

    provider_groups = []
    argument_groups = [POOL]
    return provider_groups, argument_groups


def remove_groups(parser):
    remove_group(parser)

    provider_groups = []
    argument_groups = [POOL]
    return provider_groups, argument_groups


def show_groups(parser):
    show_group(parser)

    provider_groups = []
    argument_groups = [POOL]
    return provider_groups, argument_groups


def ls_groups(parser):
    ls_group(parser)

    provider_groups = []
    argument_groups = [POOL]
    return provider_groups, argument_groups


def add_instance_groups(parser):
    add_instance_group(parser)

    provider_groups = []
    argument_groups = [INSTANCE]
    return provider_groups, argument_groups


def remove_instance_groups(parser):
    remove_instance_group(parser)

    provider_groups = []
    argument_groups = [INSTANCE]
    return provider_groups, argument_groups
