from corc.defaults import PROVIDERS, DEFAULT_PROVIDER


# TODO, might not be nessesary
# Look at deprecating the cli requirement for
# stating the provider
def valid_providers_group(parser):
    add_provider_group(parser)


def add_provider_group(parser):
    provider_group = parser.add_argument_group(title="Provider arguments")
    providers = provider_group.add_mutually_exclusive_group(required=False)

    for provider in PROVIDERS:
        if provider == DEFAULT_PROVIDER:
            providers.add_argument("{}".format(provider), action="store_true")
        else:
            providers.add_argument("{}".format(provider), action="store_true")
