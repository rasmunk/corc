from corc.config import (
    config_exists,
    get_config_path,
    load_config,
    save_config,
    generate_default_config,
    valid_config,
)
from corc.helpers import import_from_module


def prepare_provider_config(provider, provider_kwargs, **kwargs):
    prepare_config = import_from_module(
        "corc.cli.providers.{}.config".format(provider), "config", "prepare_config"
    )

    return prepare_config(provider, provider_kwargs, **kwargs)


def init_config(provider, provider_kwargs, config=None, **kwargs):
    path = get_config_path()
    if config and "path" in config:
        path = config["path"]

    response = {}
    provider_config = prepare_provider_config(provider, provider_kwargs, **kwargs)
    if not provider_config:
        response["msg"] = "Failed to generate the provider config for: {}".format(
            provider
        )
        return False, response

    # If no config exists -> create it
    _config = {}
    if not config_exists(path=path):
        _config = generate_default_config()
        save_config(_config, path=path)
    else:
        _config = load_config(path=path)

    if not config_exists(path=path):
        response["msg"] = "Failed to find a config"
        return False, response

    # Update with user arguments
    _config["corc"]["providers"].update(provider_config)

    if not save_config(_config, path=path):
        response["msg"] = "Failed to save new config"
        return False, response

    if not valid_config(_config, verbose=True):
        response["msg"] = "The generated config is invalid"
        return False, response

    response["msg"] = "Generated a new configuration"
    return True, response
