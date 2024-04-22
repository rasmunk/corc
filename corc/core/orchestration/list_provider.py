from corc.core.defaults import ORCHESTRATION
from corc.core.plugins.plugin import get_plugins
from corc.core.plugins.storage import install


async def list_providers():
    """Add a particular provider to corc."""
    # Make the provider configuration directory
    installed_providers = get_plugins(ORCHESTRATION)
    installed = install("orchestration", provider_name)
    if not installed:
        return False, {"msg": "Failed to add the provider: {}".format(provider_name)}
    return True, {"msg": "Added the provider: {}".format(provider_name)}
