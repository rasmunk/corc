from corc.providers.oci.cluster import OCIClusterOrchestrator


def prepare_options():
    oci_profile_options = dict(
        compartment_id="ocid1.tenancy.oc1..aaaaaaaakfmksyrf7hl2gfexmjpb6pbyrirm6k3ro7wd4"
        "64y2pr7atpxpv4q",
        name="XNOVOTECH",
    )
    cluster_options = dict(
        name="Test XNOVOTECH Cluster",
    )

    # Sort order in ascending to ensure that complex images
    # such as GPU powered shapes are not selected.
    # These are typically not supported by the cluster
    image_options = dict(
        operating_system="Oracle Linux",
        operating_system_version="7.8",
        limit="1",
        sort_order="ASC",
    )

    node_options = dict(
        availability_domain="Xfze:eu-amsterdam-1-AD-1",
        name="test_xnovotech_cluster",
        size=1,
        node_shape="VM.Standard1.1",
        image=image_options,
    )

    vcn_options = dict(
        cidr_block="10.0.0.0/16",
        display_name="Test XNOVOTECH Network",
        dns_label="xnovotech",
    )

    subnet_options = dict(
        cidr_block="10.0.1.0/24", display_name="workers", dns_label="workers"
    )

    options = dict(
        profile=oci_profile_options,
        cluster=cluster_options,
        node=node_options,
        vcn=vcn_options,
        subnet=subnet_options,
    )
    return options


def setup_orchestrator(options):
    OCIClusterOrchestrator.validate_options(options)
    return OCIClusterOrchestrator(options)


if __name__ == "__main__":
    options = prepare_options()
    oci_orchestrator = setup_orchestrator(options)
    oci_orchestrator.setup()
    oci_orchestrator.tear_down()
