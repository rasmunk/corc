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

import os
from importlib.metadata import entry_points
from corc.core.defaults import default_base_path, PACKAGE_NAME
from corc.utils.io import makedirs, exists


def add_provider(provider_type, name):
    """Add a particular provider to corc."""
    # Make the provider configuration directory
    provider_config_dir = os.path.join(default_base_path, provider_type)
    if not exists(provider_config_dir):
        if not makedirs(provider_config_dir):
            print(
                "Failed to create the provider configuration directory: {}".format(
                    provider_config_dir
                )
            )
            return False

    # Load and save the default configuration for the provider
    # TODO, load from the plugin
    # Find every module that defines the corc.plugins entrypoint

    # Throws KeyError if the entry point is not found
    entry_points("{}.plugins".format(PACKAGE_NAME))
    return True
