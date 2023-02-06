from corc.core.plugins.storage import install


def add_provider(provider_name, provider_type="orchestration"):
    """ Add a particular provider to corc. """
    # Make the provider configuration directory
    return install(provider_type, provider_name)
