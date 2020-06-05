import os
import oci
from oci.exceptions import CompositeOperationError, ServiceError


def _get_client_func(client, func):
    return getattr(client, func)


def _list(client, list_method_name, *args, **kwargs):
    if is_composite_client(client):
        func = _get_client_func(client.client, list_method_name)
    else:
        func = _get_client_func(client, list_method_name)
    items = perform_action(func, *args, **kwargs)
    if items:
        return items
    return []


def _perform_client_func_action(client, func_name, *args, **kwargs):
    if is_composite_client(client):
        func = _get_client_func(client.client, func_name)
    else:
        func = _get_client_func(client, func_name)
    return perform_action(func, *args, **kwargs)


def new_client(
    oci_client_class, composite_class=None, profile_name="DEFAULT", **kwargs
):
    # Try from environment, if not rely on config file
    file_location = oci.config.DEFAULT_LOCATION

    if "OCI_CONFIG_PATH" in os.environ:
        file_location = os.environ["OCI_CONFIG_PATH"]

    if "OCI_PROFILE_NAME" in os.environ:
        profile_name = os.environ["OCI_PROFILE_NAME"]

    client_config = None
    # Try to load from the config_file instead
    file_config = oci.config.from_file(
        file_location=file_location, profile_name=profile_name
    )

    # If an environment path for the key file is provided
    if "OCI_KEY_FILE" in os.environ:
        key_file = os.environ["OCI_KEY_FILE"]
        file_config.update(dict(key_file=key_file))

    oci.config.validate_config(file_config)
    client_config = file_config

    if not client_config:
        raise ValueError("The OCI client config must be loaded at this point")

    client = oci_client_class(client_config, **kwargs)
    if composite_class:
        return composite_class(client, **kwargs)
    return client


def is_composite_client(client):
    """ Composite clients have the 'client' attribute """
    return hasattr(client, "client")


def is_base_client(client):
    """Base clients have the 'base_client' attribute"""
    return hasattr(client, "base_client")


def list_entities(client, list_method, *args, **kwargs):
    return _list(client, list_method, *args, **kwargs)


def delete(client, delete_method, id, *args, wait_for_states=None, **kwargs):
    if not wait_for_states:
        wait_for_states = []

    action_kwargs = kwargs
    if is_composite_client(client):
        # Convert to the matching composite action
        pos_delete_method = "{}_and_wait_for_state".format(delete_method)
        if hasattr(client, pos_delete_method):
            delete_method = pos_delete_method
            action_kwargs["wait_for_states"] = wait_for_states
        else:
            # Fall back to the regular client since the
            # composite client dosen't have the method
            client = client.client

    func = _get_client_func(client, delete_method)
    return perform_action(func, id, **action_kwargs)


def create(client, create_method, *args, wait_for_states=None, **kwargs):
    if not wait_for_states:
        wait_for_states = []

    action_kwargs = kwargs
    if is_composite_client(client):
        # Convert to the matching composite action
        pos_create_method = "{}_and_wait_for_state".format(create_method)
        if hasattr(client, pos_create_method):
            create_method = pos_create_method
            action_kwargs["wait_for_states"] = wait_for_states
        else:
            # Fall back to the regular client since the
            # composite client dosen't have the method
            client = client.client

    func = _get_client_func(client, create_method)
    return perform_action(func, *args, **action_kwargs)


def update(client, update_method, id, wait_for_states=None, **kwargs):
    if not wait_for_states:
        wait_for_states = []

    action_kwargs = kwargs
    if is_composite_client(client):
        # Convert to the matching composite action
        pos_update_method = "{}_and_wait_for_state".format(update_method)
        if hasattr(client, pos_update_method):
            update_method = pos_update_method
            action_kwargs["wait_for_states"] = wait_for_states
        else:
            # Fall back to the regular client since the
            # composite client dosen't have the method
            client = client.client

    func = _get_client_func(client, update_method)
    return perform_action(func, id, **action_kwargs)


def get(client, get_method, id, **kwargs):
    return _perform_client_func_action(client, get_method, id, **kwargs)


def get_subnet_gateway_id(network_client, vcn_id, subnet_id, compartment_id):
    existing_subnets = network_client.list_subnets(compartment_id, vcn_id).data
    if not existing_subnets:
        return None
    for subnet in existing_subnets:
        if subnet.id != subnet_id:
            continue

        # Get the gateway of the first subnet
        subnet = existing_subnets[0]
        route_table = network_client.get_route_table(subnet.route_table_id).data
        # Find the Internet Gateway id in the first route for now
        route = route_table.route_rules[0]
    return route.network_entity_id


def prepare_route_rule(network_entity_id, **route_rule_kwargs):
    route_rule = oci.core.models.RouteRule(
        network_entity_id=network_entity_id, **route_rule_kwargs
    )
    return route_rule


def get_kubernetes_version(container_engine_client):
    """
    get_kubernetes_version

    Get the supported kubernetes versions from the service.  There are multiple
    versions supported but for the example we will just use the last one in the
    list.
    """

    if is_composite_client(container_engine_client):
        func = _get_client_func(container_engine_client.client, "get_cluster_options")
    else:
        func = _get_client_func(container_engine_client, "get_cluster_options")

    response = func(cluster_option_id="all")
    versions = response.data.kubernetes_versions
    if len(versions) > 0:
        kubernetes_version = versions[-1]
    else:
        raise RuntimeError("No supported Kubernetes versions found")

    return kubernetes_version


def stack_was_deleted(stack):
    for key_type, value_type in stack.items():
        if isinstance(value_type, (bool, str)):
            if not value_type:
                return False
        if isinstance(value_type, (list, tuple)):
            for result in value_type:
                if not result:
                    return False
    return True


def perform_action(action, *args, **kwargs):
    try:
        result = action(*args, **kwargs)
        if hasattr(result, "data"):
            return result.data
    # TODO, check for regular errors as well
    except (CompositeOperationError, ServiceError) as err:
        print("Failed to perform action: {}, err: {}".format(action, err))
        if hasattr(err, "cause"):
            print("Failed cause: {}".format(err.cause))

        return False
    return True
