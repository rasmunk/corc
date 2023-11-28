from corc.core.plugins.storage import install


def add_provider(provider_type="orchestration", provider_name=None):
    """Add a particular provider to corc."""
    # Make the provider configuration directory
    installed = install(provider_type, provider_name)
    if not installed:
        return False, {"msg": "Failed to add the provider: {}".format(provider_name)}
    return True, {"msg": "Added the provider: {}".format(provider_name)}
