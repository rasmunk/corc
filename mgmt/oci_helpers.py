import oci


def new_client(oci_client_class, profile_name="DEFAULT"):
    config = oci.config.from_file(profile_name=profile_name)
    oci.config.validate_config(config)
    return oci_client_class(config)


def get_compartment_id(compute_client, identity_client, compartment):
    compartment_id = config["tenancy"]
    identity_client.get_compartment
    compartments = identity_client.list_compartments().data
    for compartment in compartments:
        pass
    return None


def get_instance(compute_client, compartment_id):
    # compute_client = oci.core.ComputeClient(config)
    return compute_client.get_instance(compartment_id).data


def get_instances(compute_client, compartment_id, lifecycle_state=None):
    instances = compute_client.list_instances(compartment_id).data
    if lifecycle_state:
        selected_instances = []
        for instance in instances:
            if (
                isinstance(lifecycle_state, (list, tuple, set))
                and instance.lifecycle_state in lifecycle_state
            ):
                selected_instances.append(instance)
            elif (
                isinstance(lifecycle_state, str) and lifecycle_state == lifecycle_state
            ):
                selected_instances.append(instance)
        return selected_instances
    return instances


def get_images(compute_client, compartment_id):
    return compute_client.list_images(compartment_id).data


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


def create_internet_gateway(network_client, **gateway_details):
    # HACK, should dynamically get the existing gateway, But the API doesn't seem to provide this
    # Create new if nessesary
    create_ig_details = oci.core.models.CreateInternetGatewayDetails(**gateway_details)
    try:
        # Only create the gateway if no Internet Gateway exists on the vcn
        ig_response = network_client.create_internet_gateway(create_ig_details)
        return ig_response.data
    except oci.exceptions.ServiceError as service_error:
        print("An internet gateway already exists")
    return None
