from oci.core import VirtualNetworkClient, VirtualNetworkClientCompositeOperations
from oci.core.models import CreateVcnDetails, Vcn
from args import get_arguments, OCI, NETWORK
from oci_helpers import new_client, create_vcn, delete_vcn, get_vcn, list_vcn


def new_vcn_stack(
    network_client,
    compartment_id,
    name=None,
    vcn_id=None,
    cidr_block=None,
    **vcn_kwargs
):
    if not cidr_block:
        cidr_block = "10.0.0.0/16"

    if name:
        vcn_kwargs.update({"display_name": name})

    vcn = create_vcn(network_client, compartment_id, cidr_block, **vcn_kwargs)
    if not vcn:
        exit(1)

    stack = {"vcn": vcn}

    return stack


def delete_vcn_stack(network_client, compartment_id, name=None, vcn_id=None):
    if not name and not vcn_id:
        return False

    removed_stack = {}

    vcn = get_vcn(
        network_client, vcn_id=vcn_id, name=name, compartment_id=compartment_id
    )
    if vcn:
        deleted_vcn = delete_vcn(network_client, vcn.id)
        removed_stack.update({"vcn": deleted_vcn})

    # TODO create IG and Subnet

    return removed_stack


def delete_compartment_vcns(network_client, compartment_id):

    removed_vcns = []
    vcns = list_vcn(network_client, compartment_id)
    for vcn in vcns:
        # TODO, delete all subnets first

        deleted_vcn = delete_vcn(network_client, vcn.id)
        removed_vcns.append(delete_vcn)

    return removed_vcns


if __name__ == "__main__":
    args = get_arguments([OCI, NETWORK], strip_group_prefix=True)
    network_client = new_client(
        VirtualNetworkClient,
        composite_class=VirtualNetworkClientCompositeOperations,
        profile_name=args.profile_name,
    )

    stack = new_vcn_stack(
        network_client,
        args.compartment_id,
        name=args.vcn_name,
        cidr_block=args.cidr_block,
    )
    print("Create stack: {}".format(stack))

    deleted_stack = delete_vcn_stack(
        network_client, args.compartment_id, name=args.vcn_name
    )
    print("Deleted stack: {}".format(deleted_stack))

    removed_vcns = delete_compartment_vcns(network_client, args.compartment_id)
    print("Deleted vcns: {}".format(removed_vcns))
