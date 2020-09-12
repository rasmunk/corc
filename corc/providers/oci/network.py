from oci.core import VirtualNetworkClient, VirtualNetworkClientCompositeOperations
from oci.core.models import (
    CreateVcnDetails,
    Vcn,
    UpdateVcnDetails,
    UpdateInternetGatewayDetails,
)
from oci.core.models import (
    RouteTable,
    CreateRouteTableDetails,
    UpdateRouteTableDetails,
    RouteRule,
)
from oci.core.models import InternetGateway, CreateInternetGatewayDetails
from oci.core.models import SecurityList
from oci.core.models import DhcpOptions
from oci.core.models import LocalPeeringGateway
from oci.core.models import NatGateway
from oci.core.models import ServiceGateway
from oci.core.models import Subnet, CreateSubnetDetails, UpdateSubnetDetails
from oci.retry import DEFAULT_RETRY_STRATEGY
from corc.cli.args import get_arguments, OCI, VCN
from corc.helpers import is_in, exists_in_dict, find_in_dict, unset_check
from corc.providers.oci.helpers import (
    new_client,
    prepare_details,
    list_entities,
    get,
    create,
    delete,
    update,
    stack_was_deleted,
)


def new_vcn_stack(
    network_client,
    compartment_id,
    vcn_kwargs=None,
    internet_gateway_kwargs=None,
    route_table_kwargs=None,
    subnet_kwargs=None,
):
    if not vcn_kwargs:
        vcn_kwargs = {}

    if "cidr_block" not in vcn_kwargs:
        vcn_kwargs.update({"cidr_block": "10.0.0.0/16"})

    if not internet_gateway_kwargs:
        internet_gateway_kwargs = {}

    if not route_table_kwargs:
        route_table_kwargs = {}

    if not subnet_kwargs:
        subnet_kwargs = {}

    if "cidr_block" not in subnet_kwargs:
        subnet_kwargs.update(dict(cidr_block="10.0.1.0/24"))

    stack = dict(id=None, vcn=None, internet_gateways={}, subnets={})

    create_vcn_details = prepare_details(
        CreateVcnDetails, compartment_id=compartment_id, **vcn_kwargs
    )
    vcn = create_vcn(network_client, create_vcn_details)
    if not vcn:
        raise RuntimeError("Failed to create a vcn with details: {}".format(vcn_kwargs))

    stack["id"] = vcn.id
    stack["vcn"] = vcn

    create_ig_details = prepare_details(
        CreateInternetGatewayDetails,
        compartment_id=compartment_id,
        vcn_id=vcn.id,
        **internet_gateway_kwargs,
    )

    gateway = create_internet_gateway(network_client, create_ig_details)
    if not gateway:
        raise RuntimeError(
            "Failed to create internet gateway with details: {}".format(
                create_ig_details
            )
        )

    stack["internet_gateways"][gateway.id] = gateway

    # Setup the route table
    route_rules = []
    if "routerules" in route_table_kwargs:
        for route_rule in route_table_kwargs["routerules"]:
            route_rule_details = prepare_details(
                RouteRule, network_entity_id=gateway.id, **route_rule
            )
            if route_rule_details:
                route_rules.append(route_rule_details)
        route_table_kwargs.pop("routerules")

    create_rt_details = prepare_details(
        CreateRouteTableDetails,
        compartment_id=compartment_id,
        vcn_id=vcn.id,
        route_rules=route_rules,
        **route_table_kwargs,
    )

    routetable = create_route_table(network_client, create_rt_details)
    if not routetable:
        raise RuntimeError(
            "Failed to create route table with details: {}".format(create_rt_details)
        )

    # Create subnet
    create_subnet_details = prepare_details(
        CreateSubnetDetails,
        compartment_id=compartment_id,
        vcn_id=vcn.id,
        route_table_id=routetable.id,
        **subnet_kwargs,
    )

    subnet = create_subnet(network_client, create_subnet_details)
    if subnet:
        stack["subnets"][subnet.id] = subnet
    return stack


def update_vcn_stack(
    network_client,
    compartment_id,
    vcn_kwargs=None,
    internet_gateway_kwargs=None,
    route_table_kwargs=None,
    subnet_kwargs=None,
):

    if not vcn_kwargs:
        vcn_kwargs = {}

    if not internet_gateway_kwargs:
        internet_gateway_kwargs = {}

    if not route_table_kwargs:
        route_table_kwargs = {}

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
            internet_gateway_kwargs=internet_gateway_kwargs,
            route_table_kwargs=route_table_kwargs,
            subnet_kwargs=subnet_kwargs,
        )

    stack = get_vcn_stack(network_client, compartment_id, vcn.id)
    if vcn_kwargs:
        update_vcn_details = prepare_details(UpdateVcnDetails, **vcn_kwargs)
        updated_vcn = update(network_client, "update_vcn", vcn.id, update_vcn_details)
        if not updated_vcn:
            raise RuntimeError("Failed to update VCN: {}".format(vcn.id))
        stack["vcn"] = updated_vcn

    if internet_gateway_kwargs:
        existing_ig = None
        if "id" in internet_gateway_kwargs and internet_gateway_kwargs["id"]:
            existing_ig = find_in_dict(
                {"id": internet_gateway_kwargs["id"]}, stack["internet_gateways"]
            )
        elif "display_name" in internet_gateway_kwargs:
            existing_ig = find_in_dict(
                {"display_name": internet_gateway_kwargs["display_name"]},
                stack["internet_gateways"],
            )
        if existing_ig:
            update_ie_details = prepare_details(
                UpdateInternetGatewayDetails, **internet_gateway_kwargs
            )
            updated_ie = update(
                network_client,
                "update_internet_gateway",
                existing_ig.id,
                update_ie_details,
            )
            if not updated_ie:
                raise RuntimeError(
                    "Failed to update Internet Gateway: {}".format(existing_ig.id)
                )
            stack["internet_gateways"][updated_ie.id] = updated_ie
        else:
            create_ie_details = prepare_details(
                CreateInternetGatewayDetails, **internet_gateway_kwargs
            )
            ie = create_internet_gateway(network_client, create_ie_details)
            if ie:
                stack["internet_gateways"][ie.id] = ie
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
            updated_subnet = update(
                network_client,
                "update_subnet",
                existing_subnet.id,
                update_subnet_details,
            )
            if not updated_subnet:
                raise RuntimeError(
                    "Failed to update Subnet: {}".format(existing_subnet.id)
                )
            stack["subnets"][updated_subnet.id] = updated_subnet
        else:
            create_subnet_details = prepare_details(
                CreateSubnetDetails, **subnet_kwargs
            )
            subnet = create_subnet(network_client, create_subnet_details,)
            if subnet:
                stack["subnets"][subnet.id] = subnet
    return stack


def ensure_vcn_stack(
    network_client,
    compartment_id,
    vcn_kwargs=None,
    internet_gateway_kwargs=None,
    route_table_kwargs=None,
    subnet_kwargs=None,
):

    if not vcn_kwargs:
        vcn_kwargs = {}

    if not internet_gateway_kwargs:
        internet_gateway_kwargs = {}

    if not route_table_kwargs:
        route_table_kwargs = {}

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
            internet_gateway_kwargs=internet_gateway_kwargs,
            route_table_kwargs=route_table_kwargs,
            subnet_kwargs=subnet_kwargs,
        )

    stack = get_vcn_stack(network_client, compartment_id, vcn.id)
    # Validate whether the rest of the stack is a match
    # if not, add new elements to the stack
    if internet_gateway_kwargs:
        gateway = get_internet_gateway_in_vcn_stack(
            stack,
            internet_gateway_kwargs=internet_gateway_kwargs,
            optional_value_kwargs=["id", "display_name"],
        )
        if not gateway:
            create_ig_details = prepare_details(
                CreateInternetGatewayDetails,
                compartment_id=compartment_id,
                vcn_id=vcn.id,
                **internet_gateway_kwargs,
            )

            gateway = create_internet_gateway(network_client, create_ig_details)
            if not gateway:
                raise RuntimeError(
                    "Failed to create internet gateway with details: {}".format(
                        create_ig_details
                    )
                )

    if subnet_kwargs:
        subnet = get_subnet_in_vcn_stack(
            stack,
            subnet_kwargs=subnet_kwargs,
            optional_value_kwargs=["id", "display_name"],
        )
        if not subnet:
            # Add subnet that reflects subnet_kwargs to the stack
            subnet = create_subnet_stack(
                network_client,
                compartment_id,
                stack["vcn"],
                internet_gateway_kwargs=internet_gateway_kwargs,
                route_table_kwargs=route_table_kwargs,
                subnet_kwargs=subnet_kwargs,
            )
            if not subnet:
                return False
    return True


def refresh_vcn_stack(network_client, compartment_id, vcn_kwargs=None):
    if not vcn_kwargs:
        vcn_kwargs = {}

    vcn = None
    if "id" in vcn_kwargs and vcn_kwargs["id"]:
        vcn = get(network_client, "get_vcn", vcn_kwargs["id"])
    elif "display_name" in vcn_kwargs:
        vcn = get_vcn_by_name(
            network_client, compartment_id, vcn_kwargs["display_name"]
        )

    if not vcn:
        return {}

    return get_vcn_stack(network_client, compartment_id, vcn.id)


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
        if isinstance(required_igs, (list, tuple, set)):
            for required_ig in required_igs:
                if not exists_in_dict(required_ig, stack["internet_gateways"]):
                    return False
        else:
            if not exists_in_dict(required_igs, stack["internet_gateways"]):
                return False

    if required_subnets:
        if isinstance(required_subnets, (list, tuple, set)):
            for required_subnet in required_subnets:
                if not exists_in_dict(required_subnet, stack["subnets"]):
                    return False
        else:
            if not exists_in_dict(required_subnets, stack["subnets"]):
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
            network_client, "list_internet_gateways", compartment_id, vcn_id=vcn.id,
        )
    }
    subnets = {
        subnet.id: subnet
        for subnet in list_entities(
            network_client, "list_subnets", compartment_id, vcn_id=vcn.id
        )
    }
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

    for subnet_id, subnet in vcn_stack["subnets"].items():
        if subnet_id not in other_vcn_stack["subnets"]:
            return False
    return True


def get_vcn_by_name(network_client, compartment_id, display_name, **kwargs):
    vcns = list_entities(network_client, "list_vcns", compartment_id, **kwargs)
    for vcn in vcns:
        if vcn.display_name == display_name:
            return vcn
    return None


def create_vcn(network_client, create_vcn_details, wait_for_states=None, **kwargs):
    if not wait_for_states:
        wait_for_states = [Vcn.LIFECYCLE_STATE_AVAILABLE]

    vcn = create(
        network_client,
        "create_vcn",
        create_vcn_details,
        wait_for_states=wait_for_states,
        **kwargs,
    )

    if not vcn:
        return None
    return vcn


def delete_vcn_stack(network_client, compartment_id, vcn_id=None, vcn=None):
    if not vcn_id and not vcn:
        raise ValueError("Either vcn_id or vcn must be provided")

    if vcn_id:
        vcn = get(network_client, "get_vcn", vcn_id)

    remove_stack = {
        "id": False,
        "vcn": False,
        "subnets": {},
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
            network_client, "list_subnets", compartment_id, vcn_id=vcn.id
        )
        for subnet in vcn_subnets:
            deleted = delete(
                network_client,
                "delete_subnet",
                subnet.id,
                wait_for_states=[Subnet.LIFECYCLE_STATE_TERMINATED],
                retry_strategy=DEFAULT_RETRY_STRATEGY,
            )
            remove_stack["subnets"][subnet.id] = deleted

        # Delete all the routes (and disable the gateway target
        # if they are the default which means that they can't be deleted)
        routes = list_entities(
            network_client,
            "list_route_tables",
            compartment_id,
            vcn_id=vcn.id,
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
                    update_details,
                    wait_for_states=[RouteTable.LIFECYCLE_STATE_AVAILABLE],
                    retry_strategy=DEFAULT_RETRY_STRATEGY,
                )

            # Delete all non default routes
            if len(routes) > 1:
                for route in routes[1:]:
                    deleted = delete(
                        network_client,
                        "delete_route_table",
                        route.id,
                        wait_for_states=[RouteTable.LIFECYCLE_STATE_TERMINATED],
                        retry_strategy=DEFAULT_RETRY_STRATEGY,
                    )
                    remove_stack["route_tables"].append(deleted)

        # Delete all gateways (can't delete the default)
        gateways = list_entities(
            network_client,
            "list_internet_gateways",
            compartment_id,
            vcn_id=vcn.id,
            sort_by="TIMECREATED",
            sort_order="ASC",
        )
        for gateway in gateways:
            deleted = delete(
                network_client,
                "delete_internet_gateway",
                gateway.id,
                wait_for_states=[InternetGateway.LIFECYCLE_STATE_TERMINATED],
                retry_strategy=DEFAULT_RETRY_STRATEGY,
            )
            remove_stack["internet_gateways"][gateway.id] = deleted

        # Delete all security lists
        securities = list_entities(
            network_client,
            "list_security_lists",
            compartment_id,
            vcn_id=vcn.id,
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
                    retry_strategy=DEFAULT_RETRY_STRATEGY,
                )
                remove_stack["security_lists"].append(deleted)

        # Delete all DHCP options
        dhcp_options = list_entities(
            network_client,
            "list_dhcp_options",
            compartment_id,
            vcn_id=vcn.id,
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
                    retry_strategy=DEFAULT_RETRY_STRATEGY,
                )
                remove_stack["dhcp_options"].append(deleted)

        # Delete local peering gateways
        local_peering_gateways = list_entities(
            network_client, "list_local_peering_gateways", compartment_id, vcn_id=vcn.id
        )
        for local_peering_gateway in local_peering_gateways:
            deleted = delete(
                network_client,
                "delete_local_peering_gateway",
                local_peering_gateway.id,
                wait_for_states=[LocalPeeringGateway.LIFECYCLE_STATE_TERMINATED],
                retry_strategy=DEFAULT_RETRY_STRATEGY,
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
                retry_strategy=DEFAULT_RETRY_STRATEGY,
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
                retry_strategy=DEFAULT_RETRY_STRATEGY,
            )
            remove_stack["service_gateways"].append(deleted)

        # The delete_vcn defaults internally to succeed_on_not_found
        # https://github.com/oracle/oci-python-sdk/blob/bafa4f0d68be097568772cd3cda250e60cb61a0c/src/oci/core/virtual_network_client_composite_operations.py#L1758
        deleted = delete(
            network_client,
            "delete_vcn",
            vcn.id,
            wait_for_states=[Vcn.LIFECYCLE_STATE_TERMINATED],
            retry_strategy=DEFAULT_RETRY_STRATEGY,
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


def create_route_table(
    network_client, create_route_table_details, wait_for_states=None, **kwargs
):
    if not wait_for_states:
        wait_for_states = [RouteTable.LIFECYCLE_STATE_AVAILABLE]

    routetable = create(
        network_client,
        "create_route_table",
        create_route_table_details,
        wait_for_states=[RouteTable.LIFECYCLE_STATE_AVAILABLE],
        **kwargs,
    )
    if not routetable:
        return None
    return routetable


def get_route_table_by_name(
    network_client, compartment_id, vcn_id, display_name, **kwargs
):
    route_tables = list_entities(
        network_client, "list_route_tables", compartment_id, vcn_id=vcn_id, **kwargs
    )
    for routetable in route_tables:
        if routetable.display_name == display_name:
            return routetable


def create_internet_gateway(
    network_client, create_internet_gateway_details, wait_for_states=None, **kwargs
):
    if not wait_for_states:
        wait_for_states = [InternetGateway.LIFECYCLE_STATE_AVAILABLE]

    internetgateway = create(
        network_client,
        "create_internet_gateway",
        create_internet_gateway_details,
        wait_for_states=wait_for_states,
        **kwargs,
    )
    if not internetgateway:
        return None
    return internetgateway


def get_internet_gateway_by_name(
    network_client, compartment_id, vcn_id, display_name, **kwargs
):
    internet_gateways = list_entities(
        network_client,
        "list_internet_gateways",
        compartment_id,
        vcn_id=vcn_id,
        **kwargs,
    )
    for internetgateway in internet_gateways:
        if internetgateway.display_name == display_name:
            return internetgateway


def get_internet_gateway_in_vcn_stack(
    vcn_stack, internet_gateway_kwargs=None, optional_value_kwargs=None
):
    if not isinstance(vcn_stack, dict):
        return None

    if not internet_gateway_kwargs:
        internet_gateway_kwargs = {}

    if "internet_gateways" not in vcn_stack:
        return None

    if not optional_value_kwargs:
        optional_value_kwargs = {}

    matches = []
    for gateway_id, gateway in vcn_stack["internet_gateways"].items():
        match = True
        for k, v in internet_gateway_kwargs.items():
            if k in optional_value_kwargs and unset_check(v):
                continue
            if not hasattr(gateway, k):
                match = False
            if hasattr(gateway, k) and getattr(gateway, k) != v:
                match = False

        if match:
            matches.append(gateway)
    if matches:
        return matches[0]
    return None


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
        **kwargs,
    )
    if not subnet:
        return None
    return subnet


def get_subnet_by_name(network_client, compartment_id, vcn_id, display_name, **kwargs):
    subnets = list_entities(
        network_client, "list_subnets", compartment_id, vcn_id=vcn_id, **kwargs
    )
    for subnet in subnets:
        if subnet.display_name == display_name:
            return subnet


def get_subnet_in_vcn_stack(vcn_stack, subnet_kwargs=None, optional_value_kwargs=None):
    if not isinstance(vcn_stack, dict):
        return None

    if not subnet_kwargs:
        subnet_kwargs = {}

    if "subnets" not in vcn_stack:
        return None

    if not optional_value_kwargs:
        optional_value_kwargs = {}

    matches = []
    for subnet_id, subnet in vcn_stack["subnets"].items():
        match = True
        for k, v in subnet_kwargs.items():
            if k in optional_value_kwargs and unset_check(v):
                continue
            if not hasattr(subnet, k):
                match = False
            if hasattr(subnet, k) and getattr(subnet, k) != v:
                match = False

        if match:
            matches.append(subnet)
    if matches:
        return matches[0]
    return None


def create_subnet_stack(
    network_client,
    compartment_id,
    vcn,
    internet_gateway_kwargs=None,
    route_table_kwargs=None,
    subnet_kwargs=None,
    use_default_route_table=False,
):

    if not internet_gateway_kwargs:
        internet_gateway_kwargs = {}

    if not subnet_kwargs:
        subnet_kwargs = {}

    if not route_table_kwargs:
        route_table_kwargs = {}

    routetable = None

    # use_default_route -> use the default route table
    if use_default_route_table:
        routetable = get_route_table_by_name(
            network_client, compartment_id, vcn.id, "DEFAULT"
        )
    else:
        if "id" in route_table_kwargs and route_table_kwargs["id"]:
            routetable = get(
                network_client, "get_route_table", route_table_kwargs["id"]
            )
        elif (
            "display_name" in route_table_kwargs and route_table_kwargs["display_name"]
        ):
            routetable = get_route_table_by_name(
                network_client,
                compartment_id,
                vcn.id,
                route_table_kwargs["display_name"],
            )

        if not routetable:
            # Create new
            route_rules = []

            gateway = None
            if "id" in internet_gateway_kwargs and internet_gateway_kwargs["id"]:
                gateway = get(
                    network_client,
                    "get_internet_gateway",
                    internet_gateway_kwargs["id"],
                )
            elif (
                "display_name" in internet_gateway_kwargs
                and internet_gateway_kwargs["display_name"]
            ):
                gateway = get_internet_gateway_by_name(
                    network_client,
                    compartment_id,
                    vcn.id,
                    internet_gateway_kwargs["display_name"],
                )

            if not gateway:
                # Each VCN can maximum have 1 IG
                create_ig_details = prepare_details(
                    CreateInternetGatewayDetails,
                    compartment_id=compartment_id,
                    vcn_id=vcn.id,
                    **internet_gateway_kwargs,
                )

                gateway = create_internet_gateway(network_client, create_ig_details)
                if not gateway:
                    # TODO, log error
                    return None

            route_rules = []
            if "routerules" in route_table_kwargs:
                for route_rule in route_table_kwargs["routerules"]:
                    route_rule_details = prepare_details(
                        RouteRule, network_entity_id=gateway.id, **route_rule
                    )
                    if route_rule_details:
                        route_rules.append(route_rule_details)
                route_table_kwargs.pop("routerules")

            create_rt_details = prepare_details(
                CreateRouteTableDetails,
                compartment_id=compartment_id,
                vcn_id=vcn.id,
                route_rules=route_rules,
                **route_table_kwargs,
            )

            routetable = create_route_table(network_client, create_rt_details)

    if not routetable:
        # TODO, log error
        return None

    # Create subnet
    create_subnet_details = prepare_details(
        CreateSubnetDetails,
        compartment_id=compartment_id,
        vcn_id=vcn.id,
        route_table_id=routetable.id,
        **subnet_kwargs,
    )

    return create_subnet(network_client, create_subnet_details)


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
