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

from corc.core.defaults import PROVIDER_NAME
from corc.core.initializer.defaults import SUPPORTED_INITIALIZER_PROVIDERS
from corc.core.plugins.plugin import load
from corc.cli.parsers.actions import PositionalArgumentsAction


def add_provider_group(parser):
    # Add the general orchestration providers
    lower_supported_providers = (
        ",".join(SUPPORTED_INITIALIZER_PROVIDERS).lower().split(",")
    )
    parser.add_argument(
        PROVIDER_NAME,
        choices=lower_supported_providers,
        action=PositionalArgumentsAction,
    )


def list_providers_group(parser):
    pass


def remove_provider_group(parser):
    lower_supported_providers = (
        ",".join(SUPPORTED_INITIALIZER_PROVIDERS).lower().split(",")
    )

    installed_providers = []
    for provider in lower_supported_providers:
        if load(provider):
            installed_providers.append(provider)

    parser.add_argument(
        PROVIDER_NAME,
        choices=installed_providers,
        action=PositionalArgumentsAction,
    )
