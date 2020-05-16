import sys
import os

# Import base
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_path)


from orchestration.cluster import OCIClusterOrchestrator


def prepare_options():
    oci_options = dict(
        compartment_id="ocid1.tenancy.oc1..aaaaaaaakfmksyrf7hl2gfexmjpb6pbyrirm6k3ro7wd464y2pr7atpxpv4q",
        profile_name="XNOVOTECH",
    )
    cluster_options = dict(name="Test XNOVOTECH Cluster",)
    node_options = dict(
        availability_domain="Xfze:eu-amsterdam-1-AD-1",
        name="test_xnovotech_cluster",
        size=1,
        node_shape="VM.Standard2.1",
        node_image_name="Oracle-Linux-7.7"
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
        oci=oci_options,
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
    # oci_orchestrator.tear_down()
