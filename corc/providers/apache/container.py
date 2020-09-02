from libcloud.container.base import Container
from libcloud.container.providers import get_driver
from corc.orchestrator import Orchestrator


def valid_container(container):
    if not isinstance(container, Container):
        raise TypeError("The container must be of type Container")
    return True


def get_container_by_name(client, name):
    try:
        containers = client.list_containers()
    except Exception as err:
        print(err)
    for container in containers:
        if container.name == name:
            return container
    return None


def install_image(client, path):
    try:
        image = client.install_image(path)
        return image
    except Exception as err:
        print(err)
    return None


def get_image_by_name(client, name):
    try:
        images = client.list_images()
    except Exception as err:
        print(err)
    for image in images:
        if image.name == name:
            return image
    return None


default_location_config = {"name": str, "country": str, "driver": dict}

valid_location_config = {"name": "", "country": "", "driver": {}}

default_cluster_config = {"name": "cluster", "location": default_location_config}

valid_cluster_config = {"name": str, "location": dict}


class ApacheContainerOrchestrator(Orchestrator):
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
        self.container = None

    def endpoint(self, select=None):
        return self.client.host

    def get_resource(self):
        return self.resource_id, self.container

    def poll(self):
        raise NotImplementedError

    def setup(self, resource_config=None):
        if not resource_config:
            resource_config = {}

        # Ensure the image is there
        container_name = self.options["container"]["name"]
        image = install_image(self.client, self.options["container"]["image"]["name"])
        if not image:
            raise ValueError(
                "Failed to find the image: {}".format(
                    self.options["container"]["image"]["name"]
                )
            )

        existing_container = get_container_by_name(self.client, container_name)
        if existing_container:
            raise RuntimeError(
                "A container called: {} already exists".format(container_name)
            )

        container = self.client.deploy_container(
            container_name, image, **self.options["container"]["kwargs"]
        )

        if valid_container(container):
            self.resource_id, self.container = container.id, container
        else:
            raise ValueError("The new container: {} is not valid".format(container))

        if self.container and self.resource_id:
            self._is_ready = True

    def tear_down(self):
        if not self.container:
            self.container = get_container_by_name(
                self.client, self.options["container"]["name"]
            )

        if self.container:
            # Stop it then remove it
            self.client.stop_container(self.container)
            deleted = self.client.destroy_container(self.container)
            if deleted:
                self.resource_id, self.container = None, None
        else:
            self.resource_id, self.container = None, None

        if self.container:
            self._is_ready = True
        else:
            self._is_ready = False

    @classmethod
    def make_resource_config(cls, **kwargs):
        resource_config = {}
        return resource_config

    @classmethod
    def validate_options(cls, options):
        if not isinstance(options, dict):
            raise TypeError("options is not a dictionary")
