import sys

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points, import_module
else:
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


def get_plugins(plugin_type=PLUGIN_ENTRYPOINT_BASE):
    """Get all the installed plugins on the system"""
    installed_plugins = entry_points(group=plugin_type)
    return [
        Plugin(plugin.name, plugin.group, plugin.module) for plugin in installed_plugins
    ]


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
