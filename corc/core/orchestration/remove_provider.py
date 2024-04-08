from corc.core.plugins.storage import remove


async def remove_provider(provider_name):
    """Remove a particular provider from corc."""
    # Make the provider configuration directory

    removed = remove("orchestration", provider_name)
    if not removed:
        return False, {"msg": "Failed to remove the provider: {}".format(provider_name)}
    return True, {"msg": "Removed the provider: {}".format(provider_name)}
