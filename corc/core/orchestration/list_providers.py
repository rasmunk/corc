from corc.core.defaults import ORCHESTRATION
from corc.core.plugins.plugin import get_plugins, PLUGIN_ENTRYPOINT_BASE


async def list_providers():
    """Add a particular provider to corc."""
    # Make the provider configuration directory
    plugin_type = "{}.{}".format(PLUGIN_ENTRYPOINT_BASE, ORCHESTRATION)
    installed_providers = get_plugins(plugin_type=plugin_type)
    if not installed_providers:
        return False, {"msg": "Failed to list the providers."}

    plugin_names = [plugin.name for plugin in installed_providers]
    return True, {"providers": plugin_names}
