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
        node_image_name="Oracle-Linux-7.7",
        ssh_public_key="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCpRktqNSSLq1ARcMAuuTq3I8/K3CgcPJ3CVlXfU2mxg1zSrIwFOEb+foW2jUqEFcwdCmY/gI+XxBaJHxQLIqzowl0C4d6FVtbnRCfNShSbWr4p7xY0FDJvDMD7B7f7XT8zQoCX7Qnugo/afTPxz1R8mAfLFKU97Cy5zr3Bh8mW/ipgKNfH573k50Qe9CN/S9GjtGB2bGPZGSIFpQ6tfmkssBQIkmym7UxfNgQfeV/1drc02GTqH850d7jIXsMCO8XpxQaeVl/G+1/wwAxv+Nna2s143wH6MmAzrklRyb1jQ+ip/fhVF+l4Kk8a2E+DmWsBWj5vmpRLL7hS2MHPszkp rasmus@debian",
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
