from corc.defaults import (
    INSTANCE,
    VCN_INTERNETGATEWAY,
    VCN_ROUTETABLE,
    VCN_SUBNET,
    VCN,
    PROFILE,
)

from corc.cli.parsers.providers.oci.instance import (
    start_instance_group,
    instance_identity_group,
)
from corc.cli.parsers.network.vcn import vcn_identity_group, vcn_config_group


def start_instance_groups(parser):
    start_instance_group(parser)
    vcn_identity_group(parser)
    vcn_config_group(parser)

    provider_groups = [PROFILE]
    argument_groups = [
        INSTANCE,
        VCN_INTERNETGATEWAY,
        VCN_ROUTETABLE,
        VCN_SUBNET,
        VCN,
    ]
    return provider_groups, argument_groups


def stop_instance_groups(parser):
    instance_identity_group(parser)

    provider_groups = [PROFILE]
    argument_groups = [INSTANCE]
    return provider_groups, argument_groups


def get_instance_groups(parser):
    instance_identity_group(parser)

    provider_groups = [PROFILE]
    argument_groups = [INSTANCE]
    return provider_groups, argument_groups


def list_instance_groups(parser):
    return [PROFILE], []
