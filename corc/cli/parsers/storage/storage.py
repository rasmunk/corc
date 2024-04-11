from corc.core.storage.defaults import SUPPORTED_STORAGE_PROVIDERS


def add_provider_group(parser):
    provider_group = parser.add_argument_group(
        title="Add orchestration provider arguments"
    )
    providers = provider_group.add_argument_group(title="test")

    for storage_provider in SUPPORTED_STORAGE_PROVIDERS:
        providers.add_argument(storage_provider)


def remove_provider_group(parser):
    provider_group = parser.add_argument_group(
        title="Add orchestration provider arguments"
    )
    providers = provider_group.add_argument_group(title="test")

    # TODO, only list the providers that are actually installed
    for storage_provider in SUPPORTED_STORAGE_PROVIDERS:
        providers.add_argument(storage_provider)
