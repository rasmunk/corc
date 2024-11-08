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

from corc.core.defaults import PROVIDER, COMPUTE
from corc.cli.parsers.compute.compute import (
    add_provider_group,
    remove_provider_group,
)


def add_provider_groups(parser):
    add_provider_group(parser)

    provider_groups = [PROVIDER]
    argument_groups = [COMPUTE]
    skip_groups = []
    return provider_groups, argument_groups, skip_groups


def remove_provider_groups(parser):
    remove_provider_group(parser)

    provider_groups = [PROVIDER]
    argument_groups = [COMPUTE]
    skip_groups = []
    return provider_groups, argument_groups, skip_groups
