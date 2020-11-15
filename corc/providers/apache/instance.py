from libcloud.compute.base import Node, NodeAuthSSHKey, NodeAuthPassword
from corc.authenticator import SSHCredentials
from corc.orchestrator import Orchestrator
from corc.config import (
    default_config_path,
    load_from_config,
    gen_config_provider_prefix,
)
from corc.util import eprint
from corc.providers.apache.helpers import new_apache_client


def valid_instance(instance):
    if not isinstance(instance, Node):
        raise TypeError("The Instance must be of type libcloud.compute.base.Node")
    return True


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


def client_get_instance(provider, provider_kwargs, format_return=False, instance=None):
    client = new_apache_client(provider, provider_kwargs)
    found_instance = get_instance(client, instance["uuid"])
    if found_instance:
        if format_return:
            return str(found_instance), ""
        return found_instance, ""
    return None, "Failed to find an instance with: {} details".format(instance)


def get_instance(client, instance_uuid, *args, **kwargs):
    try:
        instances = client.list_nodes(*args, **kwargs)
    except Exception as err:
        eprint(err)
        return None

    for instance in instances:
        if instance.uuid == instance_uuid:
            return instance
    return None


def client_delete_instance(provider, provider_kwargs, instance=None, **kwargs):
    client = new_apache_client(provider, provider_kwargs, **kwargs)
    found_instance = get_instance(client, instance["uuid"])
    if found_instance:
        deleted = delete_instance(client, found_instance)
        if deleted:
            return found_instance.uuid, ""
        return False, "Failed to delete: {}".format(found_instance.uuid)
    return False, "Could not find: {}".format(**instance)


def delete_instance(client, instance):
    return client.destroy_node(instance)


def client_list_instances(provider, provider_kwargs, format_return=False, **kwargs):
    client = new_apache_client(provider, provider_kwargs, **kwargs)
    instances = list_instances(client)
    if format_return:
        return [str(i) for i in instances]
    return instances


def list_instances(client):
    return client.list_nodes()


default_location_config = {"name": str, "country": str, "driver": dict}

valid_location_config = {"name": "", "country": "", "driver": {}}

default_cluster_config = {"name": "cluster", "location": default_location_config}

valid_cluster_config = {"name": str, "location": dict}


class ApacheInstanceOrchestrator(Orchestrator):
    def __init__(self, options):
        super().__init__(options)
        # Setup the specific container driver provider
        if "kwargs" not in options:
            options["kwargs"] = {}

        self.client = new_apache_client(
            options["provider"], options["provider_kwargs"], **options["kwargs"]
        )
        self.instance = None

    def endpoint(self, select=None):
        # Return the endpoint that is being orchestrated
        return "127.0.0.1"

    def get_resource(self):
        return self.resource_id, self.instance

    def poll(self):
        # target_endpoint = self.endpoint()
        # if target_endpoint:
        #     if open_port(target_endpoint, self.port):
        #         self._is_reachable = True
        #         return
        # self._is_reachable = False
        self._is_reachable = True
        return

    def setup(self, resource_config=None, credentials=None):
        image = None
        instance_options = self.options["kwargs"]["instance"]

        if instance_options["image"]:
            image = self.client.get_image(instance_options["image"])
        if not image:
            raise RuntimeError(
                "Failed to find the appropriate image: {}".format(
                    instance_options["image"]
                )
            )

        size = None
        if instance_options["size"]:
            sizes = self.client.list_sizes()
            for _size in sizes:
                if _size.id == instance_options["size"]:
                    size = _size
                    break

        if not size:
            raise RuntimeError(
                "Failed to find an appropriate size: {}".format(
                    instance_options["size"]
                )
            )

        auth = None
        # Since only one auth is supported, take the first credentials
        if credentials:
            credential = credentials[0]
            if credential.password:
                auth = NodeAuthPassword(credential.password)
            if credential.public_key:
                # libcloud expected the NodeAuthSSHKey string to be a
                # 3 component string seperated by spaces
                # {type} {key} {comment}
                auth = NodeAuthSSHKey(credential.public_key)

        instance = self.client.create_node(
            instance_options["name"], size, image, auth=auth
        )
        if valid_instance(instance):
            self.instance = instance
        else:
            raise ValueError("The new instance: {} is not valid".format(instance))

        if self.instance:
            self._is_ready = True

    def tear_down(self):
        instance_options = self.options["kwargs"]["instance"]
        if not self.instance:
            self.instance = get_instance_by_name(self.client, instance_options["name"])

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
    def adapt_options(cls, **kwargs):
        options = {}
        # Find provider
        if "provider" in kwargs:
            options["provider"] = kwargs["provider"]

        if "provider_kwargs" in kwargs:
            options["provider_kwargs"] = kwargs["provider_kwargs"]

        if "kwargs" in kwargs:
            options["kwargs"] = kwargs["kwargs"]
        return options

    @classmethod
    def load_config_options(cls, provider="", path=default_config_path):
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
    def make_credentials(cls, **kwargs):
        credentials = []
        # HACK
        if "kwargs" in kwargs:
            kwargs = kwargs["kwargs"]
        if "instance" in kwargs and "ssh_authorized_key" in kwargs["instance"]:
            public_key = kwargs["instance"]["ssh_authorized_key"]
            credentials.append(SSHCredentials(public_key=public_key))
        return credentials

    @classmethod
    def validate_options(cls, options):
        if not isinstance(options, dict):
            raise TypeError("options is not a dictionary")
