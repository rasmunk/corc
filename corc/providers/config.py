from corc.config import (
    load_from_config,
    set_in_config,
    gen_config_provider_prefix,
)


# TODO, check environment variables first
def get_provider_profile(provider, config_path=None):
    profile = load_from_config(
        {"profile": {}},
        prefix=gen_config_provider_prefix((provider,)),
        path=config_path,
        allow_sub_keys=True,
    )
    if "profile" in profile:
        return profile["profile"]
    return profile


def set_provider_profile(provider, profile, config_path=None):
    return set_in_config(
        {"profile": profile},
        prefix=gen_config_provider_prefix((provider,)),
        path=config_path,
    )
