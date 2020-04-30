from oci.core import ComputeClient
from oci.identity import IdentityClient
from oci_helpers import get_instances, new_client, get_compartment_id


if __name__ == "__main__":

    compute_client = new_client(ComputeClient, profile_name="XNOVOTECH")
    identity_client = new_client(IdentityClient, profile_name="XNOVOTECH")

    compartment_id = "ocid1.tenancy.oc1..aaaaaaaakfmksyrf7hl2gfexmjpb6pbyrirm6k3ro7wd464y2pr7atpxpv4q"

    instances = get_instances(compute_client, compartment_id)
    print(instances)
