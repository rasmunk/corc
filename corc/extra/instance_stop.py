import oci
from args import get_arguments, OCI, COMPUTE
from oci_helpers import get_instances, new_client


# Stop test
if __name__ == "__main__":
    args = get_arguments([OCI, COMPUTE], strip_group_prefix=True)
    config = oci.config.from_file(profile_name=args.profile_name)
    oci.config.validate_config(config)
    identity = oci.identity.IdentityClient(config)

    compute_client = new_client(oci.core.ComputeClient, profile_name=args.profile_name)
    identity_client = new_client(
        oci.identity.IdentityClient, profile_name=args.profile_name
    )

    instances = get_instances(
        compute_client,
        args.compartment_id,
        lifecycle_state=[
            oci.core.models.Instance.LIFECYCLE_STATE_PROVISIONING,
            oci.core.models.Instance.LIFECYCLE_STATE_STARTING,
            oci.core.models.Instance.LIFECYCLE_STATE_RUNNING,
        ],
    )

    terminate_options = dict(preserve_boot_volume=False,)

    # Stop or terminate all instances
    for instance in instances:
        compute_client.terminate_instance(instance.id, **terminate_options)

    # Verify it is terminating
    terminate_instances = compute_client.list_instances(args.compartment_id).data
    terminated_states = [
        oci.core.models.Instance.LIFECYCLE_STATE_TERMINATING,
        oci.core.models.Instance.LIFECYCLE_STATE_TERMINATED,
    ]
    for instance in terminate_instances:
        assert instance.lifecycle_state in terminated_states
