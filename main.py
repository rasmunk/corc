import oci

if __name__ == "__main__":
    config = oci.config.from_file()
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

    compartment_id = "ocid1.tenancy.oc1..aaaaaaaaru2dp5sxfbjzmjbrjdjzfqcmvi3v77i2om2rrtqcojw4p6ntcaya"
    instances = compute.list_instances(compartment_id)

    # AD
    domains = identity.list_availability_domains(compartment_id)
    # TODO, look for required 
    availability_domain = domains[0]

    # Shape
    image = None
    images = compute.list_images(compartment_id)
    image = images[0]

    # TODO, ensure it is a GPU instance
    shapes = compute.list_shapes(compartment_id, image_id=image.id)
    shape = shapes[0]
    
    options = dict(
        compartment_id=compartment_id,
        availability_domain=availability_domain,
        shape=shape
    )

    launch_instance_details = oci.core.models.LaunchInstanceDetails(**options)
    response = compute.launch_instance(launch_instance_details)

    if hasattr(response, 'data'):
        instance = response.data
        