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

from corc.core.defaults import POOL
from corc.cli.parsers.orchestration.orchestration import (
    add_provider_group,
    list_providers_group,
    remove_provider_group,
)
from corc.cli.parsers.pool import (
    create_group,
    remove_group,
    show_group,
    ls_group,
    add_instance_group,
    remove_instance_group,
)


def add_provider_groups(parser):
    add_provider_group(parser)

    provider_groups = []
    argument_groups = []
    return provider_groups, argument_groups


def list_providers_groups(parser):
    list_providers_group(parser)

    provider_groups = []
    argument_groups = []
    return provider_groups, argument_groups


def remove_provider_groups(parser):
    remove_provider_group(parser)

    provider_groups = []
    argument_groups = []
    return provider_groups, argument_groups


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


def add_node_groups(parser):
    add_instance_group(parser)

    provider_groups = []
    argument_groups = [POOL]
    return provider_groups, argument_groups


def remove_node_groups(parser):
    remove_instance_group(parser)

    provider_groups = []
    argument_groups = [POOL]
    return provider_groups, argument_groups
