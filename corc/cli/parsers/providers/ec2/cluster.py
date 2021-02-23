def cluster_identity_group(parser):
    cluster_group = parser.add_argument_group(title="Cluster Identity arguments")
    cluster_group.add_argument("--cluster-uuid", default="")
    cluster_group.add_argument("--cluster-name", default="")


def start_cluster_group(parser):
    cluster_group = parser.add_argument_group(title="Cluster Start arguments")
