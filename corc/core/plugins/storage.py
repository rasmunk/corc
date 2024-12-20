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
from corc.utils.io import exists, removedirs
from corc.utils.job import run
from corc.core.config import config_exists, save_config, load_config
from corc.core.plugins.defaults import default_plugins_dir


def pip_install(plugin_name):
    """Install a particular plugin using pip"""
    cmd = ["pip", "install", plugin_name]
    result = run(cmd, capture_output=True)
    if result["error"] and result["error"] != b"":
        print(
            "Failed to install plugin: {}, error: {}".format(
                plugin_name, result["error"]
            )
        )
        return False
    return True


def pip_uninstall(plugin_name):
    """Uninstall a particular plugin using pip"""
    cmd = ["pip", "uninstall", "-y", plugin_name]
    result = run(cmd, capture_output=True)
    if not result:
        print("Failed to uninstall plugin: {}".format(plugin_name))
        return False
    return True


def get_plugin_config_path(
    plugin_type, plugin_name, plugin_directory=default_plugins_dir
):
    return os.path.join(plugin_directory, plugin_type, plugin_name, "config")


def write_plugin_storage(plugin_config_path, plugin_config):
    return save_config(plugin_config, path=plugin_config_path)


def load_plugin_storage(plugin_type, plugin_name, plugin_directory=default_plugins_dir):
    plugin_config_path = get_plugin_config_path(
        plugin_type, plugin_name, plugin_directory=plugin_directory
    )
    if config_exists(plugin_config_path):
        return load_config(plugin_config_path)
    return None


def remove_plugin_storage(
    plugin_type, plugin_name, plugin_directory=default_plugins_dir
):
    """Remove a particular plugin"""
    module_uninstalled = pip_uninstall(plugin_name)
    if not module_uninstalled:
        print("Failed to uninstall plugin: {}".format(plugin_name))
        return False

    plugin_type_directory_path = os.path.join(plugin_directory, plugin_type)
    if not exists(plugin_type_directory_path):
        print("Directory not exists: {}".format(plugin_type_directory_path))
        return True

    plugin_directory_path = os.path.join(plugin_type_directory_path, plugin_name)
    if not exists(plugin_directory_path):
        print("Directory not exists: {}".format(plugin_directory_path))
        return True

    # Remove the plugin configuration directory
    if not removedirs(plugin_directory_path, recursive=True):
        print("Failed to remove the plugin directory: {}".format(plugin_directory_path))
        return False
    return True
