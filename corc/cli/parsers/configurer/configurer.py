from corc.core.configurer.defaults import SUPPORTED_CONFIGURER_PROVIDERS


def add_provider_group(parser):
    provider_group = parser.add_argument_group(
        title="Add configurer provider arguments"
    )
    providers = provider_group.add_argument_group()
    for configurer_provider in SUPPORTED_CONFIGURER_PROVIDERS:
        providers.add_argument(configurer_provider)


def remove_provider_group(parser):
    provider_group = parser.add_argument_group(
        title="Add configurer provider arguments"
    )
    providers = provider_group.add_argument_group()
    for configurer_provider in SUPPORTED_CONFIGURER_PROVIDERS:
        providers.add_argument(configurer_provider)
