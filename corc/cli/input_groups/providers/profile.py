from corc.defaults import PROFILE
from corc.cli.helpers import import_from_module


def profile_input_groups(parser, provider):
    """ Import the providers parser profile directly """
    valid_profile_group = import_from_module(
        "corc.cli.parsers.providers.{}.profile".format(provider),
        "profile",
        "profile_group",
    )
    valid_profile_group(parser)

    provider_groups = [PROFILE]
    argument_groups = []
    return provider_groups, argument_groups