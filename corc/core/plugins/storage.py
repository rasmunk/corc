import os
from corc.utils.io import makedirs, exists, removedirs
from corc.utils.job import run
from corc.core.config import config_exists, save_config, load_config
from corc.core.plugins.defaults import default_plugins_dir
from corc.core.plugins.plugin import import_plugin, discover


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
        imported_plugin_module = import_plugin(
            configuration_module_path, return_module=True
        )
        default_plugin_config = imported_plugin_module.generate_default_config()
        return save_config(default_plugin_config, path=plugin_config_path)
    return True


def load(plugin_type, plugin_name, plugin_directory=default_plugins_dir):
    """Load a particular plugin"""
    plugin = discover(plugin_name)
    if not plugin:
        return False
    if not import_plugin(plugin.module):
        return False
    # Load plugin config
    plugin_config_path = os.path.join(
        plugin_directory, plugin_type, plugin_name, "config"
    )
    if config_exists(plugin_config_path):
        plugin.config = load_config(plugin_config_path)
    return plugin


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
