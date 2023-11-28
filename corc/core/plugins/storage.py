import os
import sys

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points, import_module
else:
    from importlib.metadata import entry_points, import_module

from corc.utils.io import makedirs, exists, removedirs
from corc.utils.job import run
from corc.core.defaults import PACKAGE_NAME
from corc.core.config import config_exists, save_config
from corc.core.plugins.defaults import default_plugins_dir
from corc.core.plugins.plugin import Plugin

PLUGIN_ENTRYPOINT_NAME = "{}.plugins".format(PACKAGE_NAME)


def discover(plugin_name):
    """Discover whether a particular plugin is available on the system"""
    installed_plugins = entry_points(group=PLUGIN_ENTRYPOINT_NAME)
    # Look through the installed modules to find the plugin
    # in question
    for installed_plugin in installed_plugins:
        if plugin_name == installed_plugin.name:
            return Plugin(
                installed_plugin.name, installed_plugin.group, installed_plugin.module
            )
    print("Could not find plugin: {}".format(plugin_name))
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


def remove_plugin(plugin_name):
    """Remove a particular plugin module"""
    plugin = discover(plugin_name)
    if not plugin:
        return True
    if hasattr(plugin.module, "__file__"):
        return removedirs(plugin.module.__file__)
    if hasattr(plugin.module, "__path__"):
        return removedirs(plugin.module.__path__)
    return False


def get_imported_plugin(plugin_name, return_module=True):
    return import_plugin(plugin_name, return_module=return_module)


def load(plugin_name):
    """Load a particular corc plugin"""
    plugin = discover(plugin_name)
    if not plugin:
        return False
    # Import the discovered plugin
    if not get_imported_plugin(plugin.name):
        return False
    return plugin


def pip_install(plugin_name):
    """Install a particular plugin using pip"""
    cmd = ["pip", "install", plugin_name]
    result = run(cmd, capture_output=True)
    if result["error"]:
        print(
            "Failed to install plugin: {}, error: {}".format(
                plugin_name, result["error"]
            )
        )
        return False
    return True


def pip_uninstall(plugin_name):
    """Uninstall a particular plugin using pip"""
    cmd = ["pip", "uninstall", plugin_name]
    result = run(cmd, capture_output=True)
    if not result:
        print("Failed to uninstall plugin: {}".format(plugin_name))
        return False
    return True


def install(plugin_type, plugin_name, plugin_directory=default_plugins_dir):
    """Installs a particular plugin"""

    module_installed = pip_install(plugin_name)
    if not module_installed:
        print("Failed to install plugin: {}".format(plugin_name))
        return False

    if not discover(plugin_name):
        print("Failed to discover plugin post installation: {}".format(plugin_name))
        return False

    plugin_type_directory_path = os.path.join(plugin_directory, plugin_type)
    if not exists(plugin_type_directory_path):
        if not makedirs(plugin_type_directory_path):
            print(
                "Failed to create the plugin directory: {}".format(
                    plugin_type_directory_path
                )
            )
            return False

    plugin_directory_path = os.path.join(plugin_type_directory_path, plugin_name)
    if not exists(plugin_directory_path):
        if not makedirs(plugin_directory_path):
            print(
                "Failed to create the plugin directory path: {}".format(
                    plugin_directory_path
                )
            )
            return False

    # Check if a configuration already exists
    plugin_config_path = os.path.join(plugin_directory_path, "config")
    if not config_exists(plugin_config_path):
        # Generate a new plugin configuration
        configuration_module_path = "{}.config".format(plugin_name)
        imported_plugin_module = get_imported_plugin(configuration_module_path)
        default_plugin_config = imported_plugin_module.generate_default_config()
        return save_config(default_plugin_config, path=plugin_config_path)
    return True


def remove(plugin_type, plugin_name, plugin_directory=default_plugins_dir):
    """Remove a particular plugin"""
    plugin = discover(plugin_name)
    if not plugin:
        print("Not loaded plugin: {} - {}".format(plugin_name, plugin_directory))
        return True

    module_uninstalled = pip_uninstall(plugin_name)
    if not module_uninstalled:
        print("Failed to uninstall plugin: {}".format(plugin_name))
        return False

    plugin_type_directory_path = os.path.join(plugin_directory, plugin_type)
    if not exists(plugin_type_directory_path):
        print("Directory not exists: {}".format(plugin_type_directory_path))
        return True

    plugin_directory_path = os.path.join(plugin_type_directory_path, plugin.name)
    if not exists(plugin_directory_path):
        print("Directory not exists: {}".format(plugin_directory_path))
        return True

    # Remove the plugin configuration directory
    if not removedirs(plugin_directory_path, recursive=True):
        print("Failed to remove the plugin directory: {}".format(plugin_directory_path))
        return False
    return True
