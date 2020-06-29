from oci.core import VirtualNetworkClient, VirtualNetworkClientCompositeOperations
from corc.providers.oci.helpers import new_client
from corc.providers.oci.network import new_vcn_stack


def prepare_options():
    oci_options = dict(
        compartment_id="ocid1.tenancy.oc1..aaaaaaaakfmksyrf7hl2gfexmjpb6pbyrirm6k3ro7wd4"
        "64y2pr7atpxpv4q",
        name="XNOVOTECH",
    )

    vcn_options = dict(
        cidr_block="10.0.0.0/16",
        display_name="Test XNOVOTECH Network",
        dns_label="xnovotech",
    )

    subnet_options = dict(
        cidr_block="10.0.1.0/24", display_name="workers", dns_label="workers"
    )

    options = dict(oci=oci_options, vcn=vcn_options, subnet=subnet_options,)
    return options


if __name__ == "__main__":
    options = prepare_options()

    network_client = new_client(
        VirtualNetworkClient,
        composite_class=VirtualNetworkClientCompositeOperations,
        name=options["oci"]["name"],
    )

    stack = new_vcn_stack(
        network_client,
        options["oci"]["compartment_id"],
        vcn_kwargs=options["vcn"],
        subnet_kwargs=options["subnet"],
    )
