from oci.container_engine import (
    ContainerEngineClient,
    ContainerEngineClientCompositeOperations,
)
from oci.container_engine.models import Cluster, CreateClusterDetails, WorkRequest
from oci.container_engine.models import NodePool, CreateNodePoolDetails
from oci_helpers import new_client, create, delete, get, list_entities
from args import get_arguments, OCI, CLUSTER, NETWORK


def new_cluster_stack(
    container_engine_client, create_cluster_details, create_node_pool_details
):

    stack = {"cluster": None, "node_pool": None}

    cluster = create_cluster(container_engine_client, create_cluster_details)

    if not cluster:
        # Cluster is required to setup the node pool
        return stack

    stack["cluster"] = cluster
    create_node_pool_details.cluster_id = cluster.id
    node_pool = create_node_pool(container_engine_client, create_node_pool_details)

    if node_pool:
        stack["node_pool"] = node_pool

    return stack


def delete_cluster(container_engine_client, cluster_id, **kwargs):
    return delete(
        container_engine_client, "delete_cluster", Cluster, cluster_id, **kwargs
    )


def create_cluster(container_engine_client, create_cluster_details):
    cluster = create(
        container_engine_client,
        "create_cluster",
        wait_for_states=[WorkRequest.STATUS_SUCCEEDED, WorkRequest.STATUS_FAILED],
        create_cluster_details=create_cluster_details,
    )

    if not cluster:
        return None
    return cluster


def delete_node_pool(container_engine_client, cluster_id, **kwargs):
    return delete(container_engine_client, "delete_node_pool", cluster_id, **kwargs)


def create_node_pool(container_engine_client, create_node_pool_details):
    node_pool = create(
        container_engine_client,
        "create_node_pool",
        wait_for_states=[WorkRequest.STATUS_SUCCEEDED, WorkRequest.STATUS_FAILED],
        create_node_pool_details=create_node_pool_details,
    )
    if not node_pool:
        return None

    return node_pool
