from corc.cli.parsers.providers.oci.cluster import (
    start_cluster_group as oci_start_cluster,
)
from corc.cli.parsers.providers.ec2.cluster import (
    start_cluster_group as ec2_start_cluster,
)
from corc.cli.parsers.providers.oci.cluster import (
    cluster_schedule_group,
    cluster_node_identity_group,
    cluster_node_group,
)


def valid_cluster_group(parser):
    cluster_schedule_group(parser)
    cluster_identity_group(parser)
    oci_start_cluster(parser)
    ec2_start_cluster(parser)
    cluster_node_group(parser)
    cluster_node_identity_group(parser)


def cluster_identity_group(parser):
    cluster_group = parser.add_argument_group(title="Cluster Identity arguments")
    cluster_group.add_argument("--cluster-id", default="")
