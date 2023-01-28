from corc.defaults import (
    PROFILE,
    CLUSTER,
    CLUSTER_NODE,
    VCN_INTERNETGATEWAY,
    VCN_ROUTETABLE,
    VCN_SUBNET,
    VCN,
)
from corc.cli.parsers.providers.oci.cluster import (
    cluster_identity_group,
    start_cluster_group,
    start_cluster_node_group,
)


def start_cluster_groups(parser):
    start_cluster_group(parser)
    start_cluster_node_group(parser)

    provider_groups = [PROFILE]
    argument_groups = [
        CLUSTER_NODE,
        CLUSTER,
        VCN_INTERNETGATEWAY,
        VCN_ROUTETABLE,
        VCN_SUBNET,
        VCN,
    ]
    return provider_groups, argument_groups


def stop_cluster_groups(parser):
    cluster_identity_group(parser)

    provider_groups = [PROFILE]
    argument_groups = [CLUSTER]
    return provider_groups, argument_groups


def get_cluster_groups(parser):
    cluster_identity_group(parser)

    provider_groups = [PROFILE]
    argument_groups = [CLUSTER]
    return provider_groups, argument_groups


def list_cluster_groups(parser):
    return [PROFILE], []
