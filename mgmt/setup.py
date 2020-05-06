import argparse
import oci
from oci.core.virtual_network_client import VirtualNetworkClient
from oci.core.virtual_network_client_composite_operations import (
    VirtualNetworkClientCompositeOperations,
)
from oci.container_engine import (
    ContainerEngineClient,
    ContainerEngineClientCompositeOperations,
)
from oci.container_engine.models import (
    CreateClusterDetails,
    CreateNodePoolDetails,
    NodePoolPlacementConfigDetails,
)
from cluster import new_cluster_stack, create_cluster, create_node_pool
from oci_helpers import (
    new_client,
    get,
    list_entities,
    get_kubernetes_version,
    get_vcn_by_name,
)
from network import new_vcn_stack, get_vcn_stack
from args import get_arguments, OCI, CLUSTER, NETWORK, VCN, SUBNET


if __name__ == "__main__":
    vcn_args = get_arguments([VCN], strip_group_prefix=True)
    subnet_args = get_arguments([SUBNET], strip_group_prefix=True)
    args = get_arguments([OCI, CLUSTER, NETWORK], strip_group_prefix=True)
    container_engine_client = new_client(
        ContainerEngineClient,
        composite_class=ContainerEngineClientCompositeOperations,
        profile_name=args.profile_name,
    )

    network_client = new_client(
        VirtualNetworkClient,
        composite_class=VirtualNetworkClientCompositeOperations,
        profile_name=args.profile_name,
    )

    stack = None

    # Find the target vcn (id or name)
    if vcn_args.id:
        stack = get_vcn_stack(network_client, args.compartment_id, vcn_args.vcn_id)

    elif vcn_args.name:
        vcn = get_vcn_by_name(network_client, args.compartment_id, vcn_args.vcn_name)
        if vcn:
            stack = get_vcn_stack(network_client, args.compartment_id, vcn.id)
        else:
            stack = new_vcn_stack(
                network_client, args.compartment_id, name=args.vcn_name
            )
    else:
        exit(1)

    if not stack:
        exit(2)

    vcn = stack["vcn"]
    subnet = stack["subnets"][0]

    if not vcn:
        print("Failed to find a vcn")
        exit(1)

    if not args.kubernetes_version:
        kubernetes_version = get_kubernetes_version(container_engine_client)
    else:
        kubernetes_version = args.kubernetes_version

    cluster = None
    existing_clusters = list_entities(
        container_engine_client, "list_clusters", args.compartment_id
    )
    for _cluster in existing_clusters:
        if _cluster.name == args.name:
            cluster = _cluster

    if not cluster:
        # Create new cluster stack
        create_cluster_details = CreateClusterDetails(
            compartment_id=args.compartment_id,
            kubernetes_version=kubernetes_version,
            name=args.name,
            vcn_id=vcn.id,
        )
        cluster = create_cluster(container_engine_client, create_cluster_details)

    node_pool_placement_config = NodePoolPlacementConfigDetails(
        availability_domain=args.node_placement_ad_domain, subnet_id=subnet.id
    )

    create_node_pool_node_config_details = oci.container_engine.models.CreateNodePoolNodeConfigDetails(
        size=args.node_size, placement_configs=[node_pool_placement_config]
    )

    # Associate
    create_node_pool_details = CreateNodePoolDetails(
        cluster_id=cluster.id,
        compartment_id=args.compartment_id,
        kubernetes_version=kubernetes_version,
        name=args.name,
        node_shape=args.node_shape,
        node_config_details=create_node_pool_node_config_details,
    )
    node_pool = create_node_pool(container_engine_client, create_node_pool_details)
    print("Stack result: {}".format(node_pool))
