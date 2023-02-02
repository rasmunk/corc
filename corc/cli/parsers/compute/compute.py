from corc.compute.defaults import SUPPORTED_COMPUTE_PROVIDERS


def add_provider_group(parser):
    provider_group = parser.add_argument_group(
        title="Add orchestration provider arguments"
    )
    providers = provider_group.add_argument_group(title="test")

    for compute_provider in SUPPORTED_COMPUTE_PROVIDERS:
        providers.add_argument(compute_provider)


def remove_provider_group(parser):
    provider_group = parser.add_argument_group(
        title="Add orchestration provider arguments"
    )
    providers = provider_group.add_argument_group(title="test")

    # TODO, only list the providers that are actually installed
    for compute_provider in SUPPORTED_COMPUTE_PROVIDERS:
        providers.add_argument(compute_provider)
