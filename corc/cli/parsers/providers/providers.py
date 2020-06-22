from corc.defaults import PROVIDERS_LOWER, DEFAULT_PROVIDER_LOWER


def valid_providers_group(parser):
    add_provider_group(parser)


def add_provider_group(parser):
    provider_group = parser.add_argument_group(title="Provider arguments")
    providers = provider_group.add_mutually_exclusive_group(required=False)

    for provider in PROVIDERS_LOWER:
        if provider == DEFAULT_PROVIDER_LOWER:
            providers.add_argument("{}".format(provider), action="store_true")
        else:
            providers.add_argument("{}".format(provider), action="store_true")
