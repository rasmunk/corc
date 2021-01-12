from corc.providers.defaults import VIRTUAL_MACHINE
from corc.providers.types import get_orchestrator
from corc.helpers import import_from_module


def start_instance(provider, provider_kwargs, **kwargs):
    response = {}
    # Get the provider orchestrator
    orchestrator_klass, options = get_orchestrator(VIRTUAL_MACHINE, provider)
    options = dict(provider=provider, provider_kwargs=provider_kwargs, kwargs=kwargs)

    instance_options = orchestrator_klass.adapt_options(**options)
    orchestrator_klass.validate_options(instance_options)
    # Prepare credentials
    credentials = orchestrator_klass.make_credentials(**instance_options)
    orchestrator = orchestrator_klass(instance_options)
    orchestrator.setup(credentials=credentials)
    orchestrator.poll()
    if not orchestrator.is_ready():
        response["msg"] = "The instance is not ready"
        return False, response

    if not orchestrator.is_reachable():
        endpoint = orchestrator.endpoint()
        response[
            "msg"
        ] = "The instance is ready at endpoint: {} but not reachable".format(endpoint)
        return False, response
    else:
        return True, response
    return False, response


def stop_instance(provider, provider_kwargs, instance={}):
    response = {}
    provider_func = import_from_module(
        "corc.providers.{}.instance".format(provider),
        "instance",
        "client_delete_instance",
    )
    deleted_id, msg = provider_func(provider, provider_kwargs, instance=instance)
    response["msg"] = msg
    if not deleted_id:
        return False, response

    response["id"] = deleted_id
    return True, response


def list_instances(provider, provider_kwargs, **kwargs):
    response = {}
    provider_func = import_from_module(
        "corc.providers.{}.instance".format(provider),
        "instance",
        "client_list_instances",
    )
    instances = provider_func(provider, provider_kwargs, format_return=True, **kwargs)
    if instances or isinstance(instances, list) and len(instances) == 0:
        response["instances"] = instances
        return True, response
    return False, response


def get_instance(provider, provider_kwargs, instance={}):
    response = {}
    provider_func = import_from_module(
        "corc.providers.{}.instance".format(provider), "instance", "client_get_instance"
    )

    instance, msg = provider_func(
        provider, provider_kwargs, format_return=True, instance=instance
    )
    response["msg"] = msg
    if instance:
        response["instance"] = instance
        return True, response
    return False, response
