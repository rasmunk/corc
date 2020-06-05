from oci.core import VirtualNetworkClient, VirtualNetworkClientCompositeOperations
from corc.oci.helpers import new_client
from corc.oci.network import delete_compartment_vcns


if __name__ == "__main__":
    compartment_id = ""
    network_client = new_client(
        VirtualNetworkClient,
        composite_class=VirtualNetworkClientCompositeOperations,
        profile_name="",
    )

    delected_vcns = delete_compartment_vcns(network_client, compartment_id)
    print(delected_vcns)
