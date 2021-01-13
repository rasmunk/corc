from corc.providers.defaults import CONTAINER_CLUSTER
from corc.providers.types import get_orchestrator
from corc.helpers import import_from_module


def start_cluster(provider, provider_kwargs, **kwargs):
    response = {}
    # Get the provider orchestrator
    orchestrator_klass, options = get_orchestrator(CONTAINER_CLUSTER, provider)
    options = dict(provider=provider, provider_kwargs=provider_kwargs, kwargs=kwargs)

    options = orchestrator_klass.adapt_options(**options)
    orchestrator_klass.validate_options(options)
    # Prepare credentials
    credentials = orchestrator_klass.make_credentials(**options)
    orchestrator = orchestrator_klass(options)
    orchestrator.setup(credentials=credentials)
    orchestrator.poll()
    if not orchestrator.is_ready():
        response["msg"] = "The cluster is not ready"
        return False, response

    if not orchestrator.is_reachable():
        endpoint = orchestrator.endpoint()
        response[
            "msg"
        ] = "The cluster is ready at endpoint: {} but not reachable".format(endpoint)
        return False, response
    else:
        return True, response
    return False, response


def stop_cluster(provider, provider_kwargs, cluster={}):
    response = {}
    provider_func = import_from_module(
        "corc.providers.{}.cluster".format(provider),
        "cluster",
        "client_delete_cluster",
    )
    deleted_id, msg = provider_func(provider, provider_kwargs, cluster=cluster)
    response["msg"] = msg
    if not deleted_id:
        return False, response

    response["id"] = deleted_id
    return True, response


def list_clusters(provider, provider_kwargs, **kwargs):
    response = {}
    provider_func = import_from_module(
        "corc.providers.{}.cluster".format(provider), "cluster", "client_list_clusters",
    )
    clusters = provider_func(provider, provider_kwargs, format_return=True, **kwargs)
    if clusters or isinstance(clusters, list) and len(clusters) == 0:
        response["clusters"] = clusters
        return True, response
    return False, response


def get_cluster(provider, provider_kwargs, cluster={}):
    response = {}
    provider_func = import_from_module(
        "corc.providers.{}.cluster".format(provider), "cluster", "client_get_cluster"
    )

    cluster, msg = provider_func(
        provider, provider_kwargs, format_return=True, cluster=cluster
    )
    response["msg"] = msg
    if cluster:
        response["cluster"] = cluster
        return True, response
    return False, response
