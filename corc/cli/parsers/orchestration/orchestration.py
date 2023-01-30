from corc.orchestration.defaults import SUPPORTED_ORCHESTRATION_PROVIDERS


def add_provider_group(parser):
    provider_group = parser.add_argument_group(
        title="Add orchestration provider arguments"
    )
    providers = provider_group.add_mutually_exclusive_group(required=False)

    for orchestration_provider in SUPPORTED_ORCHESTRATION_PROVIDERS:
        providers.add_argument(orchestration_provider)


def remove_provider_group(parser):
    provider_group = parser.add_argument_group(
        title="Add orchestration provider arguments"
    )
    providers = provider_group.add_mutually_exclusive_group(required=False)

    # TODO, only list the providers that are actually installed
    for orchestration_provider in SUPPORTED_ORCHESTRATION_PROVIDERS:
        providers.add_argument(orchestration_provider)
