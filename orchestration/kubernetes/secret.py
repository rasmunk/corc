from kubernetes import client


def prepare_secret(secret_kwargs=None):
    if not secret_kwargs:
        secret_kwargs = {}

    # attribute_map = {
    #     'api_version': 'apiVersion',
    #     'data': 'data',
    #     'kind': 'kind',
    #     'metadata': 'metadata',
    #     'string_data': 'stringData',
    #     'type': 'type'
    # }

    secret = client.V1Secret(**secret_kwargs)
    return secret


def create_secret(api_instance, secret, namespace="default"):
    api_response = api_instance.create_namespaced_secret(
        body=secret, namespace=namespace
    )
    return api_instance
