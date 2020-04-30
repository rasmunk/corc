import argparse
import oci
import sys
from oci.exceptions import ServiceError
from oci_helpers import new_client
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
        image_id=image.id
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
    selected_subnet = None
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

    test_vcn = network_client.get_vcn(selected_vcn.id).data

    gateway_details = dict(
        compartment_id=compartment_id,
        display_name="Test Gateway from SDK",
        is_enabled=True,
        vcn_id=selected_vcn.id,
    )

    # Create new if nessesary
    create_ig_details = oci.core.models.CreateInternetGatewayDetails(**gateway_details)
    try:
        # Only create the gateway if no Internet Gateway exists on the vcn
        ig_response = network_client.create_internet_gateway(create_ig_details)
    except ServiceError as service_error:
        if service_error.code == "LimitExceeded":
            ig_response = network_client.get_v

    selected_gateway = None
    if ig_response:
        selected_gateway = ig_response.data

    # Create Route table
    route_details = dict(
        cidr_block="0.0.0.0/0",
        description="SDK create route",
        network_entity_id=selected_gateway.id,
    )

    route_rules = [oci.core.models.RouteRule(**route_details)]

    route_table_details = dict(
        compartment_id=compartment_id,
        display_name="Default route (Internet)",
        route_rules=route_rules,
        vcn_id=selected_vcn.id,
    )
    create_rt_details = oci.core.models.CreateRouteTableDetails(**route_table_details)
    route_table_response = network_client.create_route_table(create_rt_details)

    subnets_response = network_client.list_subnets(
        compartment_id=compartment_id, vcn_id=selected_vcn.id
    )

    selected_subnet = None
    if subnets_response:
        subnets = subnets_response.data
        if not subnets:
            route_table = route_table_resposne.data
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
            selected_subnet = network_client.create_subnet(create_subnet_details).data
        else:
            selected_subnet = subnets[0]

    # Create vnic
    create_vnic_details = oci.core.models.CreateVnicDetails(
        subnet_id=selected_subnet.id
    )

    # Pass ssh keys
    metadata = dict(
        ssh_authorized_keys="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAV1C3nc4oSuSEjYS924O687qhSGRstuCygpIMtHKcU4 rasmus@debian"
    )

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
