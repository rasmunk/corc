from kubernetes import client


def prepare_secret(secret_kwargs=None):
    if not secret_kwargs:
        secret_kwargs = {}

    secret = client.V1Secret(**secret_kwargs)
    return secret


def create_secret(api_instance, secret, namespace="default"):
    api_response = api_instance.create_namespaced_secret(
        body=secret, namespace=namespace
    )
    return api_response


def prepare_volume(volume_kwargs=None):
    if not volume_kwargs:
        volume_kwargs = {}

    volume = client.V1Volume(**volume_kwargs)
    return volume


def create_volume(api_instance, volume, namespace="default"):
    api_response = api_instance.create_namespaced_volume(
        body=volume, namespace=namespace
    )
    return api_response


class StorageProvider:
    def __init__(self, config):
        self.config = config
        self.core_api = client.CoreV1Api()

    def provision(self):
        pass
        # Provision secrets
        # for

        # Provision volumes
