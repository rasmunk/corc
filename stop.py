import oci


if __name__ == "__main__":
    config = oci.config.from_file()
    oci.config.validate_config(config)
    identity = oci.identity.IdentityClient(config)

    user = identity.get_user(config["user"]).data
    print(user)
    regions = identity.list_regions().data

    compute = oci.core.ComputeClient(config)
    compartment_id = config["tenancy"]

    instances = compute.list_instances(compartment_id)
    if instances:
        for instance in instances:

            response = compute.instance_action(instance.id)
            if response and hasattr(response, "data"):
                state = response.data

            compute.terminate_instance()
