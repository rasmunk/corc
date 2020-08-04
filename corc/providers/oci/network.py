import oci
from oci.core import VirtualNetworkClient, VirtualNetworkClientCompositeOperations
from oci.core.models import (
    CreateVcnDetails,
    Vcn,
    UpdateVcnDetails,
    UpdateInternetGatewayDetails,
)
from oci.core.models import RouteTable, CreateRouteTableDetails, UpdateRouteTableDetails
from oci.core.models import InternetGateway, CreateInternetGatewayDetails
from oci.core.models import SecurityList
from oci.core.models import DhcpOptions
from oci.core.models import LocalPeeringGateway
from oci.core.models import NatGateway
from oci.core.models import ServiceGateway
from oci.core.models import Subnet, CreateSubnetDetails, UpdateSubnetDetails
from corc.cli.args import get_arguments, OCI, VCN
from corc.helpers import (
    is_in,
    exists_in_list,
    exists_in_dict,
    find_in_dict,
)
from corc.providers.oci.helpers import (
    new_client,
    prepare_details,
    prepare_route_rule,
    list_entities,
    get,
    create,
    delete,
    update,
    stack_was_deleted,
)


def prepare_create_subnet_details(**kwargs):
    subnet_kwargs = {k: v for k, v in kwargs.items() if hasattr(CreateSubnetDetails, k)}
    create_subnet_details = CreateSubnetDetails(**subnet_kwargs)
    return create_subnet_details


def new_vcn_stack(
    network_client, compartment_id, vcn_kwargs=None, subnet_kwargs=None,
):
    if not vcn_kwargs:
        vcn_kwargs = {}

    if "cidr_block" not in vcn_kwargs:
        vcn_kwargs.update(dict(cidr_block="10.0.0.0/16"))

    if "id" in vcn_kwargs:
        vcn_kwargs.pop("id")

    if not subnet_kwargs:
        subnet_kwargs = {}

    if "cidr_block" not in subnet_kwargs:
        subnet_kwargs.update(dict(cidr_block="10.0.1.0/24"))

    stack = dict(id=None, vcn=None, internet_gateways={}, subnets=[])
    create_vcn_details = CreateVcnDetails(compartment_id=compartment_id, **vcn_kwargs)
    vcn = create(
        network_client,
        "create_vcn",
        wait_for_states=[Vcn.LIFECYCLE_STATE_AVAILABLE],
        create_vcn_details=create_vcn_details,
    )
    if not vcn:
        raise RuntimeError("Failed to create a vcn with details: {}".format(vcn_kwargs))

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
        raise RuntimeError(
            "Failed to create internet gateway with details: {}".format(
                create_ig_details
            )
        )

    stack["internet_gateways"][gateway.id] = gateway
    # stack["internet_gateways"].append(gateway)

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

    if not route_table:
        raise RuntimeError(
            "Failed to create route table with details: {}".format(create_rt_details)
        )

    # Create subnet
    create_subnet_details = prepare_create_subnet_details(
        compartment_id=compartment_id,
        vcn_id=vcn.id,
        route_table_id=route_table.id,
        **subnet_kwargs
    )

    subnet = create_subnet(network_client, create_subnet_details)
    if subnet:
        stack["subnets"].append(subnet)
    return stack


def update_vcn_stack(
    network_client,
    compartment_id,
    vcn_kwargs=None,
    gateway_kwargs=None,
    subnet_kwargs=None,
):

    if not vcn_kwargs:
        vcn_kwargs = {}

    if not gateway_kwargs:
        gateway_kwargs = {}

    if not subnet_kwargs:
        subnet_kwargs = {}

    vcn = None
    if "id" in vcn_kwargs and vcn_kwargs["id"]:
        vcn = get(network_client, "get_vcn", vcn_kwargs["id"])
    elif "display_name" in vcn_kwargs and vcn_kwargs["display_name"]:
        vcn = get_vcn_by_name(
            network_client, compartment_id, vcn_kwargs["display_name"]
        )

    if not vcn:
        return new_vcn_stack(
            network_client,
            compartment_id,
            vcn_kwargs=vcn_kwargs,
            subnet_kwargs=subnet_kwargs,
        )

    stack = get_vcn_stack(network_client, compartment_id, vcn.id)

    update_vcn_details = prepare_details(UpdateVcnDetails, **vcn_kwargs)
    updated_vcn = update(
        network_client, "update_vcn", vcn.id, update_vcn_details=update_vcn_details
    )
    if not updated_vcn:
        raise RuntimeError("Failed to update VCN: {}".format(vcn.id))
    stack["vcn"] = updated_vcn

    if gateway_kwargs:
        existing_ig = None
        if "id" in gateway_kwargs and gateway_kwargs["id"]:
            existing_ig = find_in_dict(
                {"id": gateway_kwargs["id"]}, stack["internet_gateways"]
            )
        elif "display_name" in gateway_kwargs:
            existing_ig = find_in_dict(
                {"display_name": gateway_kwargs["display_name"]},
                stack["internet_gateways"],
            )
        if existing_ig:
            update_ie_details = prepare_details(
                UpdateInternetGatewayDetails, **gateway_kwargs
            )
            updated_ie = update(
                network_client,
                "update_internet_gateway",
                existing_ig.id,
                update_internet_gateway_details=update_ie_details,
            )
            if not updated_ie:
                raise RuntimeError(
                    "Failed to update Internet Gateway: {}".format(existing_ig.id)
                )
            stack["internet_gateways"][updated_ie.id] = updated_ie
        else:
            create_ie_details = prepare_details(
                CreateInternetGatewayDetails, **gateway_kwargs
            )
            new_ie = create(
                network_client,
                "create_internet_gateway",
                create_internet_gateway_details=create_ie_details,
            )
            if not new_ie:
                raise RuntimeError(
                    "Failed to create a new Internet Gateway on VCN: {}".format(
                        stack["vcn"].id
                    )
                )
            stack["internet_gateways"][new_ie.id] = new_ie
    if subnet_kwargs:
        existing_subnet = None
        if "id" in subnet_kwargs and subnet_kwargs["id"]:
            existing_subnet = find_in_dict(
                {"id": subnet_kwargs["id"]}, stack["subnets"]
            )
        elif "display_name" in subnet_kwargs:
            existing_subnet = find_in_dict(
                {"display_name": subnet_kwargs["display_name"]}, stack["subnets"]
            )
        if existing_subnet:
            update_subnet_details = prepare_details(
                UpdateSubnetDetails, **subnet_kwargs
            )
            updated_ie = update(
                network_client,
                "update_subnet",
                existing_subnet.id,
                update_subnet_details=update_subnet_details,
            )
            if not updated_ie:
                raise RuntimeError(
                    "Failed to update Subnet: {}".format(existing_subnet.id)
                )
        else:
            create_subnet_details = prepare_details(
                CreateSubnetDetails, **subnet_kwargs
            )
            new_subnet = create(
                network_client,
                "create_subnet",
                create_subnet_details=create_subnet_details,
            )
            if not new_subnet:
                raise RuntimeError("Failed to create a new Subnet")
    return stack


def refresh_vcn_stack(
    network_client,
    compartment_id,
    vcn_kwargs=None,
    gateway_kwargs=None,
    subnet_kwargs=None,
):
    if not vcn_kwargs:
        vcn_kwargs = {}

    if "cidr_block" not in vcn_kwargs:
        vcn_kwargs.update(dict(cidr_block="10.0.0.0/16"))

    if not gateway_kwargs:
        gateway_kwargs = {}

    if not subnet_kwargs:
        subnet_kwargs = {}

    if "cidr_block" not in subnet_kwargs:
        subnet_kwargs.update(dict(cidr_block="10.0.1.0/24"))

    # Only accept valid kwargs

    stack = dict(id=None, vcn=None, internet_gateways={}, subnets=[])

    vcn = None
    if "id" in vcn_kwargs and vcn_kwargs["id"]:
        vcn = get(network_client, "get_vcn", vcn_kwargs["id"])
    elif "display_name" in vcn_kwargs:
        vcn = get_vcn_by_name(
            network_client, compartment_id, vcn_kwargs["display_name"]
        )

    if not vcn:
        create_vcn_details = CreateVcnDetails(
            compartment_id=compartment_id, **vcn_kwargs
        )
        vcn = create(
            network_client,
            "create_vcn",
            wait_for_states=[Vcn.LIFECYCLE_STATE_AVAILABLE],
            create_vcn_details=create_vcn_details,
        )
        if not vcn:
            raise RuntimeError(
                "Failed to create a vcn with details: {}".format(vcn_kwargs)
            )

    if not vcn:
        raise RuntimeError("Failed to either retrieve or create a vcn")

    stack["id"] = vcn.id
    stack["vcn"] = vcn

    gateways = list_entities(
        network_client,
        "list_internet_gateways",
        compartment_id,
        vcn.id,
        **gateway_kwargs
    )

    if gateways:
        stack["internet_gateways"] = {gateway.id: gateway for gateway in gateways}
    else:
        # Create one
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
            raise RuntimeError(
                "Failed to create internet gateway with details: {}".format(
                    create_ig_details
                )
            )
        stack["internet_gateways"][gateway.id] = gateway
        # stack["internet_gateways"].append(gateway)

    subnets = list_entities(network_client, "list_subnets", compartment_id, vcn.id)
    if subnets:
        stack["subnets"] = subnets
    else:
        # Setup the default route table
        route_rules = []
        for gateway_id, gateway in stack["internet_gateways"].items():
            route_rule = prepare_route_rule(
                gateway_id,
                cidr_block=None,
                destination="0.0.0.0/0",
                destination_type="CIDR_BLOCK",
            )

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

        # Create new subnet
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


def valid_vcn_stack(stack, required_vcn=None, required_igs=None, required_subnets=None):
    """ Can be either """
    if not isinstance(stack, dict):
        raise TypeError("The VCN stack must be a dictionary to be valid")

    expected_fields = ["id", "vcn", "internet_gateways", "subnets"]
    for field in expected_fields:
        if field not in stack:
            return False

        if not stack[field]:
            return False

    if required_vcn:
        if not is_in(required_vcn, stack["vcn"]):
            return False

    if required_igs:
        if not exists_in_dict(required_igs, stack["internet_gateways"]):
            return False

    if required_subnets:
        if not exists_in_list(required_subnets, stack["subnets"]):
            return False
    return True


def get_vcn_stack(network_client, compartment_id, vcn_id):
    stack = {}
    vcn = get(network_client, "get_vcn", vcn_id)
    if not vcn:
        return stack
    gateways = {
        gateway.id: gateway
        for gateway in list_entities(
            network_client, "list_internet_gateways", compartment_id, vcn.id,
        )
    }
    subnets = list_entities(network_client, "list_subnets", compartment_id, vcn.id)
    stack = {
        "id": vcn.id,
        "vcn": vcn,
        "internet_gateways": gateways,
        "subnets": subnets,
    }
    return stack


def equal_vcn_stack(vcn_stack, other_vcn_stack):
    # TODO, finish it with actual equality checks
    if vcn_stack["id"] != other_vcn_stack["id"]:
        return False

    if vcn_stack["vcn"] != other_vcn_stack["vcn"]:
        return False

    if len(vcn_stack["internet_gateways"]) != len(other_vcn_stack["internet_gateways"]):
        return False

    for gateway_id, gateway in vcn_stack["internet_gateways"].items():
        if gateway_id not in other_vcn_stack["internet_gateways"]:
            return False

    if len(vcn_stack["subnets"]) != len(vcn_stack["subnets"]):
        return False

    for i, subnet in enumerate(vcn_stack["subnets"]):
        if subnet != other_vcn_stack["subnets"][i]:
            return False

    return True


def get_vcn_by_name(network_client, compartment_id, display_name, **kwargs):
    vcns = list_entities(network_client, "list_vcns", compartment_id, **kwargs)
    for vcn in vcns:
        if vcn.display_name == display_name:
            return vcn


def delete_vcn_stack(network_client, compartment_id, vcn_id=None, vcn=None):
    if not vcn_id and not vcn:
        raise ValueError("Either vcn_id or vcn must be provided")

    if vcn_id:
        vcn = get(network_client, "get_vcn", vcn_id)

    remove_stack = {
        "id": False,
        "vcn": False,
        "subnets": [],
        "route_tables": [],
        "internet_gateways": {},
        "security_lists": [],
        "dhcp_options": [],
        "local_peering_gateways": [],
        "nat_gateways": [],
        "service_gateways": [],
    }
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
            remove_stack["subnets"].append(deleted)

        # Delete all the routes (and disable the gateway target
        # if they are the default which means that they can't be deleted)
        routes = list_entities(
            network_client,
            "list_route_tables",
            compartment_id,
            vcn.id,
            sort_by="TIMECREATED",
            sort_order="ASC",
        )
        # Disable routes on the default route table
        if routes:
            # Disable all routes
            for route in routes:
                update_details = UpdateRouteTableDetails(route_rules=[])
                update(
                    network_client,
                    "update_route_table",
                    route.id,
                    wait_for_states=[RouteTable.LIFECYCLE_STATE_AVAILABLE],
                    update_route_table_details=update_details,
                )

            # Delete all non default routes
            if len(routes) > 1:
                for route in routes[1:]:
                    deleted = delete(
                        network_client,
                        "delete_route_table",
                        route.id,
                        wait_for_states=[RouteTable.LIFECYCLE_STATE_TERMINATED],
                    )
                    remove_stack["route_tables"].append(deleted)

        # Delete all gateways (can't delete the default)
        gateways = list_entities(
            network_client,
            "list_internet_gateways",
            compartment_id,
            vcn.id,
            sort_by="TIMECREATED",
            sort_order="ASC",
        )
        for gateway in gateways:
            deleted = delete(
                network_client,
                "delete_internet_gateway",
                gateway.id,
                wait_for_states=[InternetGateway.LIFECYCLE_STATE_TERMINATED],
            )
            remove_stack["internet_gateways"][gateway.id] = deleted

        # Delete all security lists
        securities = list_entities(
            network_client,
            "list_security_lists",
            compartment_id,
            vcn.id,
            sort_by="TIMECREATED",
            sort_order="ASC",
        )
        # Can't delete the detault
        if len(securities) > 1:
            for security in securities[1:]:
                deleted = delete(
                    network_client,
                    "delete_security_list",
                    security.id,
                    wait_for_states=[SecurityList.LIFECYCLE_STATE_TERMINATED],
                )
                remove_stack["security_lists"].append(deleted)

        # Delete all DHCP options
        dhcp_options = list_entities(
            network_client,
            "list_dhcp_options",
            compartment_id,
            vcn.id,
            sort_by="TIMECREATED",
            sort_order="ASC",
        )

        if len(dhcp_options) > 1:
            for dhcp_option in dhcp_options[1:]:
                deleted = delete(
                    network_client,
                    "delete_dhcp_options",
                    dhcp_option.id,
                    wait_for_states=[DhcpOptions.LIFECYCLE_STATE_TERMINATED],
                )
                remove_stack["dhcp_options"].append(deleted)

        # Delete local peering gateways
        local_peering_gateways = list_entities(
            network_client, "list_local_peering_gateways", compartment_id, vcn.id
        )
        for local_peering_gateway in local_peering_gateways:
            deleted = delete(
                network_client,
                "delete_local_peering_gateway",
                local_peering_gateway.id,
                wait_for_states=[LocalPeeringGateway.LIFECYCLE_STATE_TERMINATED],
            )
            remove_stack["local_peering_gateways"].append(deleted)

        # Delete all NAT gateways
        nat_gateways = list_entities(
            network_client, "list_nat_gateways", compartment_id, vcn_id=vcn.id
        )
        for gateway in nat_gateways:
            deleted = delete(
                network_client,
                "delete_nat_gateway",
                gateway.id,
                wait_for_states=[NatGateway.LIFECYCLE_STATE_TERMINATED],
            )
            remove_stack["nat_gateways"].append(deleted)

        # Delete Service Gateways
        service_gateways = list_entities(
            network_client, "list_service_gateways", compartment_id, vcn_id=vcn.id
        )
        for service_gateway in service_gateways:
            deleted = delete(
                network_client,
                "delete_service_gateway",
                service_gateway.id,
                wait_for_states=[ServiceGateway.LIFECYCLE_STATE_TERMINATED],
            )
            remove_stack["service_gateways"].append(deleted)

        # The delete_vcn defaults internally to succeed_on_not_found
        # https://github.com/oracle/oci-python-sdk/blob/bafa4f0d68be097568772cd3cda250e60cb61a0c/src/oci/core/virtual_network_client_composite_operations.py#L1758
        deleted = delete(
            network_client,
            "delete_vcn",
            vcn.id,
            wait_for_states=[Vcn.LIFECYCLE_STATE_TERMINATED],
        )
        remove_stack["id"] = vcn.id
        remove_stack["vcn"] = deleted
    return remove_stack


def delete_compartment_vcns(network_client, compartment_id, **kwargs):
    removed_vcns = []
    vcns = list_entities(network_client, "list_vcns", compartment_id, **kwargs)
    for vcn in vcns:
        removed_stack = delete_vcn_stack(network_client, compartment_id, vcn_id=vcn.id)
        deleted = stack_was_deleted(removed_stack)
        removed_vcns.append(deleted)
    return removed_vcns


def create_subnet(
    network_client, create_subnet_details, wait_for_states=None, **kwargs
):
    if not wait_for_states:
        wait_for_states = [Subnet.LIFECYCLE_STATE_AVAILABLE]

    subnet = create(
        network_client,
        "create_subnet",
        create_subnet_details,
        wait_for_states=wait_for_states,
        **kwargs
    )
    if not subnet:
        return None
    return subnet


def get_subnet_by_name(network_client, compartment_id, vcn_id, display_name, **kwargs):
    subnets = list_entities(
        network_client, "list_subnets", compartment_id, vcn_id, **kwargs
    )
    for subnet in subnets:
        if subnet.display_name == display_name:
            return subnet


if __name__ == "__main__":
    vcn_args = get_arguments([VCN], strip_group_prefix=True)
    args = get_arguments([OCI], strip_group_prefix=True)
    network_client = new_client(
        VirtualNetworkClient,
        composite_class=VirtualNetworkClientCompositeOperations,
        name=args.name,
    )

    removed_vcns = delete_compartment_vcns(network_client, args.compartment_id)
    print("Deleted vcns: {}".format(removed_vcns))
