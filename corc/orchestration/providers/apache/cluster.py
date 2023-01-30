from libcloud.container.base import ContainerCluster
from libcloud.container.providers import get_driver
from corc.orchestrator import Orchestrator


def valid_cluster(cluster):
    if not isinstance(cluster, ContainerCluster):
        raise TypeError("The Cluster stack must be a ContainerCluster")


def get_cluster_by_name(client, name):
    try:
        clusters = client.list_clusters()
    except Exception as err:
        print(err)
    for cluster in clusters:
        if cluster.name == name:
            return cluster
    return None


def client_list_clusters(provider, provider_kwargs, format_return=False, **kwargs):
    raise NotImplementedError


def client_delete_cluster(provider, provider_kwargs, cluster=None):
    raise NotImplementedError


def client_get_cluster(provider, provider_kwargs, format_return=False, cluster=None):
    raise NotImplementedError


default_location_config = {"name": str, "country": str, "driver": dict}

valid_location_config = {"name": "", "country": "", "driver": {}}

default_cluster_config = {"name": "cluster", "location": default_location_config}

valid_cluster_config = {"name": str, "location": dict}


class ApacheClusterOrchestrator(Orchestrator):
    def __init__(self, options):
        super().__init__(options)

        # Setup the specific container driver provider
        if "driver" not in options:
            raise KeyError("key: 'driver' must be specified")

        if "args" in options["driver"]:
            driver_args = options["driver"]["args"]
        else:
            driver_args = tuple()

        if "kwargs" in options["driver"]:
            driver_kwargs = options["driver"]["kwargs"]
        else:
            driver_kwargs = {}

        cls = get_driver(options["driver"]["provider"])
        self.client = cls(*driver_args, **driver_kwargs)
        self.cluster = None

    def endpoint(self, select=None):
        raise NotImplementedError

    def poll(self):
        raise NotImplementedError

    def setup(self):
        cluster = self.client.create_cluster(self.options["cluster"]["name"])
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
