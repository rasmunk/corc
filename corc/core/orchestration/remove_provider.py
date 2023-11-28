from corc.core.plugins.storage import remove


def remove_provider(provider_type="orchestration", provider_name=None):
    """Remove a particular provider from corc."""
    # Make the provider configuration directory

    removed = remove(provider_type, provider_name)
    if not removed:
        return False, {"msg": "Failed to remove the provider: {}".format(provider_name)}
    return True, {"msg": "Removed the provider: {}".format(provider_name)}
