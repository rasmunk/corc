from corc.core.orchestration.defaults import (
    ORCHESTRATION_PROVIDER_NAME,
    SUPPORTED_ORCHESTRATION_PROVIDERS,
)
from corc.core.plugins.plugin import load
from corc.cli.parsers.actions import PositionalArgumentsAction


def add_provider_group(parser):
    # Add the general orchestration providers
    lower_supported_providers = (
        ",".join(SUPPORTED_ORCHESTRATION_PROVIDERS).lower().split(",")
    )
    parser.add_argument(
        ORCHESTRATION_PROVIDER_NAME,
        choices=lower_supported_providers,
        action=PositionalArgumentsAction,
    )


def remove_provider_group(parser):
    lower_supported_providers = (
        ",".join(SUPPORTED_ORCHESTRATION_PROVIDERS).lower().split(",")
    )

    installed_providers = []
    for provider in lower_supported_providers:
        if load(provider):
            installed_providers.append(provider)

    parser.add_argument(
        ORCHESTRATION_PROVIDER_NAME,
        choices=installed_providers,
        action=PositionalArgumentsAction,
    )
