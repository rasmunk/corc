import os
import sys

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points, import_module
else:
    from importlib.metadata import entry_points, import_module

from corc.core.defaults import PACKAGE_NAME
from corc.core.io import makedirs, exists
from corc.core.config import config_exists, save_config
from corc.core.plugins.defaults import default_plugins_dir

PLUGIN_ENTRYPOINT_NAME = "{}_plugin".format(PACKAGE_NAME)


def discover(plugin_name):
    """ Discover whether a particular plugin is available on the system """
    installed_plugins = entry_points(group=PLUGIN_ENTRYPOINT_NAME)
    # Look through the installed modules to find the plugin
    # in question
    for plugin in installed_plugins:
        if plugin_name in plugin:
            return plugin
    print("Could not find plugin: {}".format(plugin_name))
    return False


def load(plugin_name):
    """ Load a particular corc plugin """
    plugin = discover(plugin_name)
    if not plugin:
        return False
    # Import the discovered plugin
    try:
        import_module(plugin)
    except (ImportError, TypeError):
        raise RuntimeError("Failed to load plugin: {}".format(plugin_name))

    return True


def install(plugin_type, plugin_name, install_destination=default_plugins_dir):
    """ Installs a particular plugin """
    # Make the plugin configuration directory
    plugin = discover(plugin_name)
    if not plugin:
        # TODO, maybe try and install it??
        return False

    plugin_config_dir = os.path.join(install_destination, plugin_type)
    if not exists(plugin_config_dir):
        if not makedirs(plugin_config_dir):
            print(
                "Failed to create the plugin configuration directory: {}".format(
                    plugin_config_dir
                )
            )
            return False

    # Check if a configuration already exists
    plugin_config_path = os.path.join(plugin_config_dir, plugin_name)
    if not config_exists(plugin_config_path):
        # Generate a new plugin configuration
        default_plugin_config = plugin.generate_default_config()
        return save_config(default_plugin_config)
    return True
