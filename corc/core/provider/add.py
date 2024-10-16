import os
from importlib.metadata import entry_points
from corc.core.defaults import default_base_path
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
    entry_points("corc.plugins")
    return True
