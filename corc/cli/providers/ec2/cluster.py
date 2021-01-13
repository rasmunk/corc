from corc.defaults import PROFILE, CLUSTER
from corc.cli.parsers.cluster.cluster import cluster_identity_group
from corc.cli.parsers.providers.ec2.cluster import start_cluster_group


def start_cluster_groups(parser):
    start_cluster_group(parser)

    provider_groups = [PROFILE]
    argument_groups = [
        CLUSTER,
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
