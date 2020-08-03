from libcloud.compute.base import Node
from libcloud.compute.providers import get_driver
from corc.orchestrator import Orchestrator
from corc.config import (
    load_from_config,
    gen_config_provider_prefix,
)


def valid_instance(instance):
    if not isinstance(instance, Node):
        raise TypeError("The Instance must be of type libcloud.compute.base.Node")


def get_instance_by_name(client, name):
    try:
        instances = client.list_nodes()
    except Exception as err:
        print(err)
        return None

    if instances:
        for instance in instances:
            if instance.name == name:
                return instance
    return None


default_location_config = {"name": str, "country": str, "driver": dict}

valid_location_config = {"name": "", "country": "", "driver": {}}

default_cluster_config = {"name": "cluster", "location": default_location_config}

valid_cluster_config = {"name": str, "location": dict}


class ApacheInstanceOrchestrator(Orchestrator):
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
        self.instance = None

    def endpoint(self, select=None):
        raise NotImplementedError

    def poll(self):
        raise NotImplementedError

    def setup(self):
        # TODO, find the image to run
        # images = self.client.list_images()
        # image = self.client.get_image("")
        instance = self.client.create_node(*self.options["instance"]["args"])
        if valid_instance(instance):
            self.instance = instance
        else:
            raise ValueError("The new instance: {} is not valid".format(instance))

        if self.instance:
            self._is_ready = True

    def tear_down(self):
        if not self.instance:
            self.instance = get_instance_by_name(
                self.client, self.options["compute"]["name"]
            )

        if self.instance:
            deleted = self.client.destroy_node(self.instance)
            if deleted:
                self.instance = None
        else:
            self.instance = None

        if self.instance:
            self._is_ready = True
        else:
            self._is_ready = False

    @classmethod
    def load_config_options(cls, provider="", path=None):
        options = {}
        provider_prefix = ("apache", provider)

        apache_profile = load_from_config(
            {"profile": {}},
            prefix=gen_config_provider_prefix(provider_prefix),
            path=path,
        )

        if "profile" in apache_profile:
            options["profile"] = apache_profile["profile"]

        return options

    @classmethod
    def validate_options(cls, options):
        if not isinstance(options, dict):
            raise TypeError("options is not a dictionary")
