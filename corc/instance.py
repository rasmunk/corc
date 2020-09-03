from oci.util import to_dict
from corc.providers.oci.instance import (
    list_instances as oci_list_instances,
    delete_instance as oci_delete_instance,
    get_instance as oci_get_instance,
    get_instance_by_name as oci_get_instance_by_name,
)
from corc.providers.oci.instance import OCIInstanceOrchestrator, new_compute_client


def start_instance(provider_kwargs, instance={}, vcn={}):
    response = {}
    if provider_kwargs:

        internetgateway = vcn.pop("internetgateway", {})
        routetable = vcn.pop("routetable", {})
        subnet = vcn.pop("subnet", {})

        instance_options = dict(
            profile=provider_kwargs["profile"],
            instance=instance,
            vcn=vcn,
            internetgateway=internetgateway,
            routetable=routetable,
            subnet=subnet,
        )
        OCIInstanceOrchestrator.validate_options(instance_options)
        orchestrator = OCIInstanceOrchestrator(instance_options)

        orchestrator.setup()
        orchestrator.poll()
        if not orchestrator.is_ready():
            response["msg"] = "The instance is not ready"
            return False, response

        if not orchestrator.is_reachable():
            response["msg"] = "The instance is ready but not reachable"
            return False, response

        return True, response
    return False, response


def stop_instance(provider_kwargs, instance={}):
    response = {}
    if provider_kwargs:
        # Discover the vcn_stack for the cluster
        if not instance["id"] and not instance["display_name"]:
            response[
                "msg"
            ] = "Either the id or display-name of the instance must be provided"
            return False, response

        compute_client = new_compute_client(name=provider_kwargs["profile"]["name"])
        if instance["id"]:
            instance_id = instance["id"]
        else:
            instance_object = oci_get_instance_by_name(
                compute_client,
                provider_kwargs["profile"]["compartment_id"],
                instance["display_name"],
            )
            instance_id = instance_object.id

        response["id"] = instance_id
        deleted = oci_delete_instance(compute_client, instance_id)
        if not deleted:
            response["msg"] = "Failed to delete: {}".format(instance_id)
            return False, response
        return True, response


def list_instances(provider_kwargs):
    response = {}
    if provider_kwargs:
        client = new_compute_client(name=provider_kwargs["profile"]["name"])
        instances = oci_list_instances(
            client, provider_kwargs["profile"]["compartment_id"]
        )
        response["instances"] = to_dict(instances)
        return True, response
    return False, response


def get_instance(provider_kwargs, instance={}):
    response = {}
    if provider_kwargs:
        if not instance["id"] and not instance["display_name"]:
            response["msg"] = "Either the id or name of the instance must be provided"
            return False, response
        client = new_compute_client(name=provider_kwargs["profile"]["name"])
        if instance["id"]:
            instance_id = instance["id"]
            instance = oci_get_instance(
                client, provider_kwargs["profile"]["compartment_id"], instance_id
            )
        else:
            instance = oci_get_instance_by_name(
                client,
                provider_kwargs["profile"]["compartment_id"],
                instance["display_name"],
            )
        response["instance"] = to_dict(instance)
        return True, response
    return False, response
