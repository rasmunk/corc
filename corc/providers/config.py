from corc.config import load_config, load_from_config, gen_config_provider_prefix


def get_profile(provider, config=None):
    profile = load_from_config(
        {"profile": {}}, prefix=gen_config_provider_prefix((provider,)), config=config,
    )
    return profile
