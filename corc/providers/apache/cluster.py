from libcloud.container.base import ContainerCluster, ClusterLocation
from libcloud.container.providers import get_driver
from corc.orchestrator import Orchestrator


def valid_cluster(cluster):
    if not isinstance(cluster, ContainerCluster):
        raise TypeError("The Cluster stack must be a ContainerCluster")


def get_cluster_by_name(client, name):
    clusters = client.list_clusters()
    for cluster in clusters:
        if cluster.name == name:
            return cluster
    return None


default_location_config = {"name": str, "country": str, "driver": dict}

valid_location_config = {"name": "", "country": "", "driver": {}}

default_cluster_config = {"name": "cluster", "location": default_location_config}

valid_cluster_config = {"name": str, "location": dict}


class ApacheClusterOrchestrator(Orchestrator):
    def __init__(self, options):
        super().__init__options(options)

        self.options = options
        # Setup the specific container driver provider
        if "driver" not in options:
            raise KeyError("key: 'driver' must be specified")

        if "kwargs" not in options:
            raise KeyError("key: 'kwargs' must be specified")

        cls = get_driver(options["driver"]["name"])
        self.client = cls(options["driver"]["kwargs"])
        self.cluster = None

    def endpoint(self, select=None):
        raise NotImplementedError

    def poll(self):
        raise NotImplementedError

    def setup(self):
        cluster = self.client.create_cluster(**self.options["cluster"])
        if valid_cluster(cluster):
            self.cluster = cluster
        else:
            raise ValueError("The new cluster: {} is not valid".format(cluster))

        if self.cluster:
            self._is_ready = True

    def tear_down(self):
        if not self.cluster:
            self.cluster = get_cluster_by_name(
                self.client, self.options["cluster"]["name"]
            )

        if self.cluster:
            deleted = self.client.destroy_cluster(self.cluster)
            if deleted:
                self.cluster = None
        else:
            self.cluster = None

        if self.cluster:
            self._is_ready = True
        else:
            self._is_ready = False

    @classmethod
    def validate_options(cls, options):
        if not isinstance(options, dict):
            raise TypeError("options is not a dictionary")

        required_cluster_fields = {"name": str}
