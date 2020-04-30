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
