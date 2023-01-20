from corc.defaults import PROFILE, CONFIG
from corc.cli.parsers.providers.libvirt.profile import (
    profile_group
)

def profile_groups(parser):
    profile_group(parser)

    provider_groups = [PROFILE]
    argument_groups = []
    return provider_groups, argument_groups
