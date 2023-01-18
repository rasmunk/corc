from corc.providers.config import generate_config, valid_config


def prepare_config(provider, provider_kwargs, **kwargs):
    # Expects that the default corc config is present
    config = {provider: {}}
    config[provider].update(provider_kwargs)
    config = generate_config(provider, **kwargs)
    if not valid_config(provider, config, verbose=True):
        return False
    return config
