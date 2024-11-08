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

from corc.core.configurer.defaults import SUPPORTED_CONFIGURER_PROVIDERS


def add_provider_group(parser):
    provider_group = parser.add_argument_group(
        title="Add configurer provider arguments"
    )
    providers = provider_group.add_argument_group()
    for configurer_provider in SUPPORTED_CONFIGURER_PROVIDERS:
        providers.add_argument(configurer_provider)


def remove_provider_group(parser):
    provider_group = parser.add_argument_group(
        title="Add configurer provider arguments"
    )
    providers = provider_group.add_argument_group()
    for configurer_provider in SUPPORTED_CONFIGURER_PROVIDERS:
        providers.add_argument(configurer_provider)
