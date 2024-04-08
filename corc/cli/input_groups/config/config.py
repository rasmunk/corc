from corc.core.defaults import PROFILE, CONFIG
from corc.cli.parsers.config.config import valid_config_args_groups


def config_input_groups(parser):
    valid_config_args_groups(parser)

    provider_groups = [PROFILE]
    argument_groups = [CONFIG]
    skip_groups = []
    return provider_groups, argument_groups, skip_groups
