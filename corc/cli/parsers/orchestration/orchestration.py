from corc.core.orchestration.defaults import (
    ORCHESTRATION_PROVIDER,
    SUPPORTED_ORCHESTRATION_PROVIDERS,
)


def add_provider_group(parser):
    # Add the general orchestration providers
    lower_supported_providers = (
        ",".join(SUPPORTED_ORCHESTRATION_PROVIDERS).lower().split(",")
    )
    parser.add_argument(ORCHESTRATION_PROVIDER, choices=lower_supported_providers)


def remove_provider_group(parser):
    lower_supported_providers = (
        ",".join(SUPPORTED_ORCHESTRATION_PROVIDERS).lower().split(",")
    )
    parser.add_argument(
        ORCHESTRATION_PROVIDER, choices=lower_supported_providers,
    )
