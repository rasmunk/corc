from corc.core.plugins.storage import install


async def add_provider(provider_name):
    """Add a particular provider to corc."""
    # Make the provider configuration directory
    installed = install("orchestration", provider_name)
    if not installed:
        return False, {"msg": "Failed to add the provider: {}".format(provider_name)}
    return True, {"msg": "Added the provider: {}".format(provider_name)}
