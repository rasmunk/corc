import oci
from oci.core import VirtualNetworkClient, VirtualNetworkClientCompositeOperations
from oci.core.models import CreateVcnDetails, Vcn
from oci.core.models import RouteTable, CreateRouteTableDetails, UpdateRouteTableDetails
from oci.core.models import InternetGateway
from oci.core.models import SecurityList
from oci.core.models import DhcpOptions
from oci.core.models import LocalPeeringGateway
from oci.core.models import NatGateway
from oci.core.models import ServiceGateway
from oci.core.models import Subnet, CreateSubnetDetails
from orchestration.args import get_arguments, OCI, SUBNET, VCN
from orchestration.oci_helpers import (
    new_client,
    prepare_route_rule,
    list_entities,
    get,
    create,
    delete,
    update,
)


def new_vcn_stack(
    network_client, compartment_id, vcn_kwargs=None, subnet_kwargs=None,
):
    if not vcn_kwargs:
        vcn_kwargs = dict(cidr_block="10.0.0.0/16")

    if not subnet_kwargs:
        subnet_kwargs = dict(cidr_block="10.0.1.0/24")

    stack = dict(id=None, vcn=None, internet_gateways=[], subnets=[])
    create_vcn_details = CreateVcnDetails(compartment_id=compartment_id, **vcn_kwargs)
    vcn = create(
        network_client,
        "create_vcn",
        wait_for_states=[Vcn.LIFECYCLE_STATE_AVAILABLE],
        create_vcn_details=create_vcn_details,
    )
    if not vcn:
        print("Failed to create vcn")
        exit(1)

    stack["id"] = vcn.id
    stack["vcn"] = vcn

    create_ig_details = oci.core.models.CreateInternetGatewayDetails(
        compartment_id=compartment_id, is_enabled=True, vcn_id=vcn.id
    )
    gateway = create(
        network_client,
        "create_internet_gateway",
        wait_for_states=[InternetGateway.LIFECYCLE_STATE_AVAILABLE],
        create_internet_gateway_details=create_ig_details,
    )
    if not gateway:
        print("Failed to create gateway")
        exit(1)
    stack["internet_gateways"].append(gateway)

    # Setup the route table
    route_rule = prepare_route_rule(
        gateway.id,
        cidr_block=None,
        destination="0.0.0.0/0",
        destination_type="CIDR_BLOCK",
    )

    route_rules = []
    if route_rule:
        route_rules.append(route_rule)

    create_rt_details = CreateRouteTableDetails(
        compartment_id=compartment_id, route_rules=route_rules, vcn_id=vcn.id
    )
    route_table = create(
        network_client,
        "create_route_table",
        wait_for_states=[RouteTable.LIFECYCLE_STATE_AVAILABLE],
        create_route_table_details=create_rt_details,
    )

    # Create subnet
    create_subnet_details = CreateSubnetDetails(
        compartment_id=compartment_id,
        vcn_id=vcn.id,
        route_table_id=route_table.id,
        **subnet_kwargs
    )
    subnet = create(
        network_client,
        "create_subnet",
        wait_for_states=[Subnet.LIFECYCLE_STATE_AVAILABLE],
        create_subnet_details=create_subnet_details,
    )

    if subnet:
        stack["subnets"].append(subnet)

    return stack


def valid_vcn_stack(stack):

    if not isinstance(stack, dict):
        raise TypeError("The VCN stack must be a dictionary to be valid")

    expected_fields = ["id", "vcn", "internet_gateways", "subnets"]
    for field in expected_fields:
        if field not in stack:
            return False
    return True


def get_vcn_stack(
    network_client, compartment_id, vcn_id, subnet_kwargs=None, gateway_kwargs=None
):

    if not subnet_kwargs:
        subnet_kwargs = dict()

    if not gateway_kwargs:
        gateway_kwargs = dict()

    stack = {}
    vcn = get(network_client, "get_vcn", vcn_id)
    if not vcn:
        return stack
    subnets = list_entities(
        network_client, "list_subnets", compartment_id, vcn.id, **subnet_kwargs
    )
    gateways = list_entities(
        network_client,
        "list_internet_gateways",
        compartment_id,
        vcn.id,
        **gateway_kwargs
    )
    stack = {
        "id": vcn.id,
        "vcn": vcn,
        "internet_gateways": gateways,
        "subnets": subnets,
    }
    return stack


def get_vcn_by_name(network_client, compartment_id, display_name, **kwargs):
    vcns = list_entities(network_client, "list_vcns", compartment_id, **kwargs)
    for vcn in vcns:
        if vcn.display_name == display_name:
            return vcn


def delete_vcn_stack(network_client, compartment_id, display_name=None, vcn_id=None):
    if not display_name and not vcn_id:
        return False

    if vcn_id:
        vcn = get(network_client, "get_vcn", vcn_id)
    else:
        # TODO, use get_vcn_by_name
        # Find vcns with the name
        vcns = list_entities(
            network_client, "list_vcns", compartment_id, display_name=display_name
        )
        vcn = vcns[0]

    removed_stack = {}
    if vcn:
        vcn_subnets = list_entities(
            network_client, "list_subnets", compartment_id, vcn.id
        )
        for subnet in vcn_subnets:
            deleted = delete(
                network_client,
                "delete_subnet",
                subnet.id,
                wait_for_states=[Subnet.LIFECYCLE_STATE_TERMINATED],
            )

        # Delete all the routes (and disable the gateway target if they are the default which
        # means that they can't be deleted)
        routes = list_entities(
            network_client, "list_route_tables", compartment_id, vcn.id
        )
        for route in routes:
            update_details = UpdateRouteTableDetails(route_rules=[])
            update(
                network_client,
                "update_route_table",
                route.id,
                wait_for_states=[RouteTable.LIFECYCLE_STATE_AVAILABLE],
                update_route_table_details=update_details,
            )

            delete(
                network_client,
                "delete_route_table",
                route.id,
                wait_for_states=[RouteTable.LIFECYCLE_STATE_TERMINATED],
            )

        # Delete all gateways
        gateways = list_entities(
            network_client, "list_internet_gateways", compartment_id, vcn.id
        )
        for gateway in gateways:
            delete(
                network_client,
                "delete_internet_gateway",
                gateway.id,
                wait_for_states=[InternetGateway.LIFECYCLE_STATE_TERMINATED],
            )

        # Delete all security lists
        securities = list_entities(
            network_client, "list_security_lists", compartment_id, vcn.id
        )
        for security in securities:
            delete(
                network_client,
                "delete_security_list",
                security.id,
                wait_for_states=[SecurityList.LIFECYCLE_STATE_TERMINATED],
            )

        # Delete all DHCP options
        dhcp_options = list_entities(
            network_client, "list_dhcp_options", compartment_id, vcn.id
        )
        for dhcp_option in dhcp_options:
            delete(
                network_client,
                "delete_dhcp_options",
                dhcp_option.id,
                wait_for_states=[DhcpOptions.LIFECYCLE_STATE_TERMINATED],
            )

        # Delete local peering gateways
        local_peering_gateways = list_entities(
            network_client, "list_local_peering_gateways", compartment_id, vcn.id
        )
        for local_peering_gateway in local_peering_gateways:
            delete(
                network_client,
                "delete_local_peering_gateway",
                local_peering_gateway.id,
                wait_for_states=[LocalPeeringGateway.LIFECYCLE_STATE_TERMINATED],
            )

        # Delete all NAT gateways
        nat_gateways = list_entities(
            network_client, "list_nat_gateways", compartment_id, vcn_id=vcn.id
        )
        for gateway in nat_gateways:
            delete(
                network_client,
                "delete_nat_gateway",
                gateway.id,
                wait_for_states=[NatGateway.LIFECYCLE_STATE_TERMINATED],
            )

        # Delete Service Gateways
        service_gateways = list_entities(
            network_client, "list_service_gateways", compartment_id, vcn_id=vcn.id
        )
        for service_gateway in service_gateways:
            delete(
                network_client,
                "delete_service_gateway",
                service_gateway.id,
                wait_for_states=[ServiceGateway.LIFECYCLE_STATE_TERMINATED],
            )

        error = delete(
            network_client,
            "delete_vcn",
            vcn.id,
            wait_for_states=[Vcn.LIFECYCLE_STATE_TERMINATED],
        )
        if not error:
            removed_stack.update({"vcn": vcn.id})
    # TODO create IG and Subnet
    return removed_stack


def delete_compartment_vcns(network_client, compartment_id, **kwargs):
    removed_vcns = []
    vcns = list_entities(network_client, "list_vcns", compartment_id, **kwargs)
    for vcn in vcns:
        result = delete_vcn_stack(network_client, compartment_id, vcn_id=vcn.id)
        removed_vcns.append(result)
    return removed_vcns


if __name__ == "__main__":
    vcn_args = get_arguments([VCN], strip_group_prefix=True)
    subnet_args = get_arguments([SUBNET], strip_group_prefix=True)
    args = get_arguments([OCI], strip_group_prefix=True)
    network_client = new_client(
        VirtualNetworkClient,
        composite_class=VirtualNetworkClientCompositeOperations,
        profile_name=args.profile_name,
    )

    # stack = new_vcn_stack(
    #     network_client,
    #     args.compartment_id,
    #     name=vcn_args.vcn_name,
    #     vcn_kwargs=vars(vcn_args),
    #     subnet_kwargs=vars(subnet_args),
    # )
    # print("Create stack: {}".format(stack))

    # deleted_stack = delete_vcn_stack(
    #     network_client, args.compartment_id, display_name=vcn_args.display_name
    # )
    # print("Deleted stack: {}".format(deleted_stack))

    removed_vcns = delete_compartment_vcns(network_client, args.compartment_id)
    print("Deleted vcns: {}".format(removed_vcns))
