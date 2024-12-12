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

import sys
from importlib.metadata import entry_points, import_module
from corc.utils.io import removedirs
from corc.core.defaults import PACKAGE_NAME

PLUGIN_ENTRYPOINT_BASE = "{}.plugins".format(PACKAGE_NAME)


class Plugin:
    """Contains the relevant plugin data for corc"""

    def __init__(self, name, group, module, config=None):
        self.name = name
        self.group = group
        self.module = module
        self.config = config

    def as_dict(self):
        return {
            "name": self.name,
            "group": self.group,
            "module": self.module,
            "config": self.config,
        }


def get_python_entrypoints(entry_point_group):
    """Get all the installed plugins on the system"""
    # Python 3.9 and below does not support group selection
    # https://docs.python.org/3.9/library/importlib.metadata.html#entry-points
    if sys.version_info <= (3, 10):
        available_entrypoints = entry_points()
        found_entrypoints = available_entrypoints.get(entry_point_group, [])
    else:
        # https://docs.python.org/3.10/library/importlib.metadata.html#entry-points
        found_entrypoints = entry_points(group=entry_point_group)
    return found_entrypoints


def get_plugins(plugin_type=PLUGIN_ENTRYPOINT_BASE):
    """Get all the installed plugins on the system"""
    installed_plugins = get_python_entrypoints(plugin_type)
    return [
        Plugin(plugin.name, plugin.group, plugin.module) for plugin in installed_plugins
    ]


def get_plugin_cli_module_path_and_name(
    plugin_name,
    plugin_type=PLUGIN_ENTRYPOINT_BASE,
    plugin_cli_entrypoint="console_scripts"
):
    """Get the module path for the cli module in a particular plugin"""
    console_scripts_entrypoints = get_python_entrypoints(plugin_cli_entrypoint)
    for console_script in console_scripts_entrypoints:
        # Get the module path for the console script and remove the function name within the module after the colon
        module_path, function_name = console_script.value.split(":")
        if module_path.startswith(plugin_name):
            return module_path, function_name
    return False, False


def discover(plugin_name, plugin_type=PLUGIN_ENTRYPOINT_BASE):
    """Discover whether a particular plugin is available on the system"""
    installed_plugins = get_plugins(plugin_type=plugin_type)
    # Look through the installed modules to find the plugin
    # in question
    for installed_plugin in installed_plugins:
        if plugin_name == installed_plugin.name:
            return installed_plugin
    return False


def import_plugin(plugin_name, return_module=False):
    imported_module = None
    try:
        imported_module = import_module(plugin_name)
    except (ImportError, TypeError):
        raise RuntimeError("Failed to load plugin: {}".format(plugin_name))
    if return_module:
        return imported_module
    return True


def remove_plugin(plugin_name, plugin_type=PLUGIN_ENTRYPOINT_BASE):
    """Remove a particular plugin module"""
    plugin = discover(plugin_name, plugin_type=plugin_type)
    if not plugin:
        return True
    if hasattr(plugin.module, "__file__"):
        return removedirs(plugin.module.__file__)
    if hasattr(plugin.module, "__path__"):
        return removedirs(plugin.module.__path__)
    return False


def load(plugin_name, plugin_type=PLUGIN_ENTRYPOINT_BASE):
    """Load a particular corc plugin"""
    plugin = discover(plugin_name, plugin_type=plugin_type)
    if not plugin:
        return False
    # Import the discovered plugin
    if not import_plugin(plugin.name):
        return False
    return plugin
