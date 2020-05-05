import argparse
from oci.container_engine.models import Cluster, CreateClusterDetails
from oci.container_engine.models import NodePool, CreateNodePoolDetails
from oci.core.virtual_network_client import VirtualNetworkClient
from oci.core.virtual_network_client_composite_operations import (
    VirtualNetworkClientCompositeOperations,
)
from oci.container_engine import (
    ContainerEngineClient,
    ContainerEngineClientCompositeOperations,
)
from oci_helpers import new_client, create, get, list_entities, get_kubernetes_version
from network import new_vcn_stack
from args import get_arguments, OCI, CLUSTER, NETWORK


if __name__ == "__main__":
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

    if args.vcn_id:
        vcn = get(network_client, 'get_vcn', args.vcn_id)
    else:
        vcns = list_entities(network_client, 'list_vcns', args.compartment_id)
        if not vcns:
            stack = new_vcn_stack(network_client, args.compartment_id,
                                vcn_cidr_block=args.vcn_cidr_block,
                                vcn_subnet_cidr_block=args.vcn_subnet_cidr_block)
            vcns.append(stack['vnc'])
        if args.vcn_name:
            # name is not unique, so might return multiple vcns
            for _vcn in vcns:
                if _vcn.name == args.vcn_name:
                    vcn = _vcn
                    break
        else:
            # HACK: Pick the first vcn
            vcn = vcns[0]

    if not vcn:
        print("Failed to find a vcn")
        exit(1)

    if not args.kubernetes_version:
        kubernetes_version = get_kubernetes_version(container_engine_client)

    cluster_details = CreateClusterDetails(
        compartment_id=args.compartment_id,
        kubernetes_version=kubernetes_version,
        vcn_id=vcn.id
    )
    cluster = create(container_engine_client, 'create_cluster', Cluster, create_cluster_details=cluster_details)

    if not cluster:
        print("Failed to create cluster")
        exit(1)

    create_np_details = CreateNodePoolDetails(
        cluster_id=cluster.id,
        compartment_id=args.compartment_id,
        kubernetes_version=kubernetes_version,
        name=args.cluster_name,
        node_shape=node_shape
    )

    node_pool = create(container_engine_client, 'create_node_pool', NodePool, create_node_pool_details=create_np_details)
    if not node_pool:
        print("Failed to create node pool")
        exit(1)

