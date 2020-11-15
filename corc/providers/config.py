import flatten_dict
from corc.config import (
    default_config_path,
    load_from_config,
    set_in_config,
    gen_config_provider_prefix,
    recursive_check_config,
)
from corc.helpers import import_from_module


# TODO, check environment variables first
def get_provider_profile(provider, config_path=default_config_path):
    profile = load_from_config(
        {"profile": {}},
        prefix=gen_config_provider_prefix((provider,)),
        path=config_path,
        allow_sub_keys=True,
    )
    if "profile" in profile:
        return profile["profile"]
    return profile


def set_provider_profile(provider, profile, config_path=default_config_path):
    return set_in_config(
        {"profile": profile},
        prefix=gen_config_provider_prefix((provider,)),
        path=config_path,
    )


def generate_config(provider, overwrite_with_empty=False, **kwargs):
    load_default_config = import_from_module(
        "corc.providers.{}.config".format(provider), "config", "load_default_config",
    )

    default_config = load_default_config(provider)
    if kwargs:
        flat = flatten_dict.flatten(default_config)
        other_flat = flatten_dict.flatten(kwargs)
        for k, v in other_flat.items():
            if not v and overwrite_with_empty:
                flat[k] = v
            if v:
                flat[k] = v
        default_config = flatten_dict.unflatten(flat)
    return default_config


def valid_config(provider, config, verbose=False):
    if not isinstance(config, dict):
        return False

    if provider not in config:
        return False

    provider_valid_config = load_valid_config(provider)
    return recursive_check_config(
        config[provider], provider_valid_config, verbose=verbose
    )


def get_provider_config_groups(provider):
    return load_config_groups(provider)


def load_config_groups(provider):
    config_groups_loader = import_from_module(
        "corc.providers.{}.config".format(provider), "config", "load_config_groups"
    )
    return config_groups_loader(provider=provider)


def load_default_config(provider):
    default_config = import_from_module(
        "corc.providers.{}.config".format(provider), "config", "load_default_config"
    )
    return default_config(provider=provider)


def load_valid_config(provider):
    valid_config = import_from_module(
        "corc.providers.{}.config".format(provider), "config", "load_valid_config"
    )
    return valid_config(provider=provider)
