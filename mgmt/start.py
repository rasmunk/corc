import argparse
import oci
import sys
from oci.exceptions import ServiceError
from oci_helpers import new_client, create_internet_gateway, get_subnet_gateway_id
from conf import get_arguments


if __name__ == "__main__":
    args = get_arguments()
    config = oci.config.from_file(profile_name=args.profile_name)
    oci.config.validate_config(config)
    identity = oci.identity.IdentityClient(config)

    user = identity.get_user(config["user"]).data
    regions = identity.list_regions().data
    compute_client = oci.core.ComputeClient(config)

    if args.compartment_id:
        compartment_id = args.compartment_id
    else:
        compartment_id = config["tenancy"]

    instances = compute_client.list_instances(compartment_id)

    # AD
    availability_domain = None
    domains = identity.list_availability_domains(compartment_id)
    if domains:
        availability_domain = domains.data[0]
    # TODO, look for required

    # Shape
    operating_system = "Oracle Linux"
    operating_system_version = "7.8"
    target_shape = "VM.Standard2.1"

    selected_image = None
    images_response = compute_client.list_images(compartment_id)
    if images_response:
        images = images_response.data
        for image in images:
            if (
                image.operating_system == operating_system
                and image.operating_system_version == operating_system_version
            ):
                selected_image = image

    instance_source_via_image_details = oci.core.models.InstanceSourceViaImageDetails(
        image_id=selected_image.id
    )

    # TODO, ensure it is a GPU instance
    selected_shape = None
    shapes_response = compute_client.list_shapes(
        compartment_id, image_id=selected_image.id
    )
    if shapes_response:
        shapes = shapes_response.data
        for shape in shapes:
            if shape.shape == target_shape:
                selected_shape = shape

    network_client = oci.core.VirtualNetworkClient(config)
    vcn_cidr_block = "10.0.0.0/16"

    # List vcns
    selected_vcn = None
    vcns_response = network_client.list_vcns(compartment_id)
    if vcns_response:
        vcns = vcns_response.data
        if not vcns:
            # Create new vcn
            vcn_details = dict(compartment_id=compartment_id, cidr_block=vcn_cidr_block)
            create_vcn_details = oci.core.models.CreateVcnDetails(**vcn_details)
            vcn_response = network_client.create_vcn(create_vcn_details)
            if vcn_response:
                selected_vcn = vcn_response.data
        else:
            selected_vcn = vcns[0]

    if not selected_vcn:
        print("No VCN is available")
        exit(1)

    # If any subnets exists -> use the first one
    selected_subnet = None
    gateway_id = None
    existing_subnets = network_client.list_subnets(
        args.compartment_id, selected_vcn.id
    ).data
    if existing_subnets:
        selected_subnet = existing_subnets[0]
        gateway_id = get_subnet_gateway_id(
            network_client, selected_vcn.id, selected_subnet.id, args.compartment_id
        )

    if not gateway_id:
        gateway_details = dict(
            compartment_id=compartment_id, is_enabled=True, vcn_id=selected_vcn.id
        )

        # No gateway exists in the existing
        gateway = create_internet_gateway(network_client, **gateway_details)
        if not gateway:
            exit(1)

        # Create Route Rules
        route_details = dict(
            cidr_block="0.0.0.0/0",
            description="SDK create route",
            network_entity_id=gateway.id,
        )
        route_rules = [oci.core.models.RouteRule(**route_details)]
        route_table_details = dict(
            compartment_id=compartment_id,
            display_name="Default route (Internet)",
            route_rules=route_rules,
            vcn_id=selected_vcn.id,
        )

        # Create RouteTable
        create_rt_details = oci.core.models.CreateRouteTableDetails(
            **route_table_details
        )
        route_table_response = network_client.create_route_table(create_rt_details)
        subnets_response = network_client.list_subnets(
            compartment_id=compartment_id, vcn_id=selected_vcn.id
        )

        # Assign route table to the subnet
        selected_subnet = None
        if subnets_response:
            subnets = subnets_response.data
            if not subnets:
                route_table = route_table_response.data
                # Create a new subnet
                cidr_block = "10.0.0.0/24"
                subnet_details = dict(
                    compartment_id=compartment_id,
                    cidr_block=cidr_block,
                    route_table_id=route_table.id,
                    vcn_id=selected_vcn.id,
                )
                create_subnet_details = oci.core.models.CreateSubnetDetails(
                    **subnet_details
                )
                selected_subnet = network_client.create_subnet(
                    create_subnet_details
                ).data
            else:
                selected_subnet = subnets[0]
    else:
        subnets = network_client.list_subnets(args.compartment_id, selected_vcn.id).data
        selected_subnet = subnets[0]

    if not selected_subnet:
        print("Failed to find a valid subnet")
        exit(1)

    # Create vnic
    create_vnic_details = oci.core.models.CreateVnicDetails(
        subnet_id=selected_subnet.id
    )

    metadata = {}
    if args.ssh_authorized_keys:
        metadata.update({
            'ssh_authorized_keys': '\n'.join(args.ssh_authorized_keys)
        })

    options = dict(
        compartment_id=compartment_id,
        availability_domain=availability_domain.name,
        shape=selected_shape.shape,
        create_vnic_details=create_vnic_details,
        source_details=instance_source_via_image_details,
        metadata=metadata,
    )

    launch_instance_details = oci.core.models.LaunchInstanceDetails(**options)
    launch_response = compute_client.launch_instance(launch_instance_details)

    good_states = [
        oci.core.models.Instance.LIFECYCLE_STATE_PROVISIONING,
        oci.core.models.Instance.LIFECYCLE_STATE_STARTING,
        oci.core.models.Instance.LIFECYCLE_STATE_RUNNING,
    ]
    if launch_response:
        instance = launch_response.data
        if instance.lifecycle_state not in good_states:
            print(
                "Instance launch state: {} is not in: {}".format(
                    instance.lifecycle_state, good_states
                )
            )
            exit(2)

        # Get public ip
        public_ip = instance.metadata
