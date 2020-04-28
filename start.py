import oci

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
    print(len(compartments))

    compute.list_instances(compartment_id)
    for compartment in compartments:    
        try:
            instances = compute.list_instances(compartment.id)
            print(instances)
        except oci.exceptions.ServiceError:
            print("Failed")

    print("Compartments: {}".format(identity.list_compartments(compartment_id).data))

    compartment_id = "ocid1.tenancy.oc1..aaaaaaaaaw4lzr5ypcuimzmklu6ttdau4xn45n72ohgs4afcmwqpwcxgm7ca"
    instances = compute.list_instances(compartment_id)

    # AD
    availability_domain = None
    domains = identity.list_availability_domains(compartment_id)
    if domains:
        availability_domain = domains.data[0]
    # TODO, look for required 

    # Shape
    operating_system = 'Oracle Linux'
    operating_system_verison = '7.8'
    target_shape = 'VM.Standard2.1'

    selected_image = None
    images_response = compute.list_images(compartment_id)
    if images_response:
        images = images_response.data
        for image in images:
            if image.operating_system == operating_system \
                and image.operating_system_version == operating_system_verison:
                selected_image = image

    instance_source_via_image_details = oci.core.models.InstanceSourceViaImageDetails(
        image_id=image.id
    )

    # TODO, ensure it is a GPU instance
    selected_shape = None
    shapes_response = compute.list_shapes(compartment_id, image_id=selected_image.id)
    if shapes_response:
        shapes = shapes_response.data
        for shape in shapes:
            if shape.shape == target_shape:
                selected_shape = shape
    

    network_client = oci.core.VirtualNetworkClient(config)
    vcn_cidr_block = '172.16.0.0/16'

    # List vcns
    selected_vcn = None
    selected_subnet = None
    vcns_response = network_client.list_vcns(compartment_id)
    if vcns_response:
        vcns = vcns_response.data
        if not vcns:
            # Create new vcn
            vcn_details = dict(
                compartment_id=compartment_id,
                cidr_block=vcn_cidr_block
            )
            create_vcn_details = oci.core.models.CreateVcnDetails(**vcn_details)
            vcn_response = network_client.create_vcn(create_vcn_details)
            if vcn_response:
                selected_vcn = vcn_response.data
        else:
            selected_vcn = vcns[0]

    if not selected_vcn:
        print("Not VCN is available")
        exit(1)

    subnets_response = network_client.list_subnets(
        compartment_id=compartment_id,
        vcn_id=selected_vcn.id
    )

    selected_subnet = None
    if subnets_response:
        subnets = subnets_response.data
        if not subnets:
            # Create a new subnet
            cidr_block = '172.16.1.0/24'
            subnet_details = dict(
                compartment_id=compartment_id,
                cidr_block=cidr_block,
                vcn_id=selected_vcn.id
            )
            create_subnet_details = oci.core.models.CreateSubnetDetails(**subnet_details)
            selected_subnet = network_client.create_subnet(create_subnet_details).data
        else:
            selected_subnet = subnets[0]

    # Create vcn
    create_vnic_details = oci.core.models.CreateVnicDetails(
        subnet_id=selected_subnet.id
    )

    options = dict(
        compartment_id=compartment_id,
        availability_domain=availability_domain.name,
        shape=selected_shape.shape,
        create_vnic_details=create_vnic_details,
        source_details=instance_source_via_image_details
    )

    launch_instance_details = oci.core.models.LaunchInstanceDetails(**options)
    launch_response = compute.launch_instance(launch_instance_details)

    good_states = [
        oci.core.models.Instance.LIFECYCLE_STATE_PROVISIONING,
        oci.core.models.Instance.LIFECYCLE_STATE_STARTING,
        oci.core.models.Instance.LIFECYCLE_STATE_RUNNING
    ]
    if launch_response:
        launch = launch_response.data
        if launch.lifecycle_state not in good_states:
            print("Instance launch state: {} is not in: {}".format(launch.lifecycle_state,
                                                                   good_states))
            exit(2)
