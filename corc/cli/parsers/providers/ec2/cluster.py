def cluster_identity_group(parser):
    cluster_group = parser.add_argument_group(title="Cluster Identity arguments")
    cluster_group.add_argument("--cluster-uuid", default="")


def start_cluster_group(parser):
    _ = parser.add_argument_group(title="Cluster Start arguments")
