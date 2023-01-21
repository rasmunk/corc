from corc.cli.helpers import import_from_module


def add_provider_parse_profile_groups(parser, provider):
    """ Import the providers parser profile directly """
    parser_profile_group = import_from_module(
        "corc.cli.parsers.providers.{}.profile".format(provider),
        "profile",
        "profile_group",
    )
    return parser_profile_group(parser)
