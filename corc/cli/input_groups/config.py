from corc.defaults import PROFILE, CONFIG
from corc.cli.parsers.providers.libvirt.profile import profile_group

def config_groups(parser):
    
    provider_groups = [PROFILE]
    argument_groups = [CONFIG]
    return provider_groups, argument_groups