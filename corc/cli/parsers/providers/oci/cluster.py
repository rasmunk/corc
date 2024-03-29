def cluster_identity_group(parser):
    cluster_group = parser.add_argument_group(title="Cluster Identity arguments")
    cluster_group.add_argument("--cluster-id", default="")
    cluster_group.add_argument("--cluster-name", default="")


def start_cluster_group(parser):
    cluster_group = parser.add_argument_group(title="Cluster Start arguments")
    cluster_group.add_argument("--cluster-kubernetes-version", default="")
    cluster_group.add_argument("--cluster-domain", default="")
    cluster_group.add_argument("--cluster-name", default="")


def start_cluster_node_group(parser):
    node_group = parser.add_argument_group(title="Cluster Node Start arguments")
    node_group.add_argument("--cluster-node-name", default="")
    node_group.add_argument("--cluster-node-availability-domain", default="")
    node_group.add_argument("--cluster-node-size", type=int)
    node_group.add_argument("--cluster-node-node-shape", default="")
    # https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/api/cims/models/oci.cims.models.CreateResourceDetails.html?highlight=availability_domain#oci.cims.models.CreateResourceDetails.availability_domain
    node_group.add_argument("--cluster-node-image", default="")


def cluster_node_identity_group(parser):
    node_group = parser.add_argument_group(title="Cluster Node Identity")
    node_group.add_argument("--cluster-node-id", default="")


def cluster_schedule_group(parser):
    cluster_group = parser.add_argument_group(title="Cluster Runtime arguments")
    cluster_group.add_argument("--cluster-image", default="")
