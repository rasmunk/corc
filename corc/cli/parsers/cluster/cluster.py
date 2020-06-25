def valid_cluster_group(parser):
    cluster_schedule_group(parser)
    select_cluster_group(parser)
    start_cluster_group(parser)


def cluster_schedule_group(parser):
    cluster_group = parser.add_argument_group(title="Cluster Runtime arguments")
    cluster_group.add_argument(
        "--cluster-image", default=""
    )


def select_cluster_group(parser):
    cluster_group = parser.add_argument_group(title="Cluster Identity arguments")
    cluster_group.add_argument("--cluster-id", default="")
    cluster_group.add_argument("--cluster-name", default="")


def start_cluster_group(parser):
    cluster_group = parser.add_argument_group(title="Cluster Start arguments")
    cluster_group.add_argument("--cluster-kubernetes-version", default=None)
    cluster_group.add_argument("--cluster-domain", default="")
