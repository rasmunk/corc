import oci


# Stop test
if __name__ == "__main__":
    config = oci.config.from_file(profile_name="RASMUSMUNK")
    oci.config.validate_config(config)
    identity = oci.identity.IdentityClient(config)

    user = identity.get_user(config['user']).data
    print(user)
    regions = identity.list_regions().data

    compute = oci.core.ComputeClient(config)
    compartment_id = config['tenancy']
    compartments = identity.list_compartments(compartment_id).data

    compute.list_instances(compartment_id)
    for compartment in compartments:    
        try:
            instances = compute.list_instances(compartment.id)
            print(instances)
        except oci.exceptions.ServiceError:
            print("Failed")

    print("Compartments: {}".format(identity.list_compartments(compartment_id).data))

    compartment_id = "ocid1.tenancy.oc1..aaaaaaaaaw4lzr5ypcuimzmklu6ttdau4xn45n72ohgs4afcmwqpwcxgm7ca"
    instances = compute.list_instances(compartment_id).data
    terminate_options = dict(
        preserve_boot_volume=False,
    )

    # Stop or terminate all instances
    for instance in instances:
        compute.terminate_instance(instance.id, **terminate_options)

    # Verify it is terminating
    terminate_instances = compute.list_instances(compartment_id).data
    terminated_states = [
        oci.core.models.Instance.LIFECYCLE_STATE_TERMINATING,
        oci.core.models.Instance.LIFECYCLE_STATE_TERMINATED
    ]
    for instance in terminate_instances:
        assert instance.lifecycle_state in terminated_states
