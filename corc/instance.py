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
    response["id"] = orchestrator.resource_id
    if not orchestrator.is_ready():
        response["msg"] = "The instance is not ready"
        return False, response

    endpoints = orchestrator.endpoints()
    if not orchestrator.is_reachable():
        response[
            "msg"
        ] = "The instance is ready at endpoints: {} but not yet reachable".format(
            endpoints
        )
        return True, response
    else:
        response["msg"] = "The instance is ready at endpoints: {} and reachable".format(
            endpoints
        )
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


def get_instance(provider, provider_kwargs, instance={}, details={}):
    response = {}
    provider_func = import_from_module(
        "corc.providers.{}.instance".format(provider), "instance", "client_get_instance"
    )

    instance_id, instance, msg = provider_func(
        provider,
        provider_kwargs,
        format_return=True,
        instance=instance,
        details=details,
    )
    response["id"] = instance_id
    response["msg"] = msg
    if instance:
        response["instance"] = instance
        return True, response
    return False, response
