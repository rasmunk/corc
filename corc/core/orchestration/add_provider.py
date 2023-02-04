import os
import sys
import sys

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

from corc.core.defaults import default_base_path
from corc.core.io import write, makedirs, exists
from corc.core.helpers import import_from_module


def add_provider(provider_type=None, provider_name=None):
    """ Add a particular provider to corc. """
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
    discovered_plugins = entry_points("corc.plugins")

    return True
