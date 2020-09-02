from oci.util import to_dict
from corc.providers.oci.cluster import (
    list_clusters as oci_list_clusters,
    delete_cluster_stack as oci_delete_cluster_stack,
    get_cluster_by_name as oci_get_cluster_by_name,
    get_cluster_stack as oci_get_cluster_stack,
)
from corc.providers.oci.cluster import (
    OCIClusterOrchestrator,
    new_cluster_engine_client,
)


def list_clusters(provider_kwargs):
    response = {}
    if provider_kwargs:
        container_engine_client = new_cluster_engine_client(
            name=provider_kwargs["profile"]["name"]
        )
        clusters = oci_list_clusters(
            container_engine_client, provider_kwargs["profile"]["compartment_id"]
        )
        response["clusters"] = []
        for cluster in clusters:
            cluster_stack = oci_get_cluster_stack(
                container_engine_client,
                provider_kwargs["profile"]["compartment_id"],
                cluster.id,
            )
            response["clusters"].append(to_dict(cluster_stack))
        return True, response
    return False, response


def start_cluster(provider_kwargs, cluster={}, vcn={}):
    # Interpolate general arguments with config
    response = {}
    if provider_kwargs:
        # Node shape is special
        if "shape" in cluster["node"]:
            cluster["node"]["node_shape"] = cluster["node"]["shape"]
            cluster["node"].pop("shape")

        # (Adapt) Split VCN, Internet Gateway, RouteTable, RouteRules and Subnet
        subnet = vcn.pop("subnet", {})
        internetgateway = vcn.pop("internetgateway", {})
        routetable = vcn.pop("routetable", {})

        cluster_options = dict(
            profile=provider_kwargs["profile"],
            cluster=cluster,
            vcn=vcn,
            internetgateway=internetgateway,
            routetable=routetable,
            subnet=subnet,
        )

        OCIClusterOrchestrator.validate_options(cluster_options)
        orchestrator = OCIClusterOrchestrator(cluster_options)
        # TODO, poll if the cluster already exists
        orchestrator.setup()
        orchestrator.poll()
        if not orchestrator.is_ready():
            response["msg"] = "The cluster is not ready"
            return False, response

        if not orchestrator.is_reachable():
            response["msg"] = "The cluster is ready but not reachable"
            return False, response

        return True, response
    return False, response


def stop_cluster(provider_kwargs, cluster={}):
    response = {}
    if provider_kwargs:
        # Discover the vcn_stack for the cluster
        if not cluster["id"] and not cluster["name"]:
            response["msg"] = "Either the id or name of the cluster must be provided"
            return False, response

        container_engine_client = new_cluster_engine_client(
            name=provider_kwargs["profile"]["name"]
        )
        if cluster["id"]:
            cluster_id = cluster["id"]
        else:
            cluster_object = oci_get_cluster_by_name(
                container_engine_client,
                provider_kwargs["profile"]["compartment_id"],
                cluster["name"],
            )
            cluster_id = cluster_object.id

        response["id"] = cluster_id
        deleted = oci_delete_cluster_stack(container_engine_client, cluster_id)
        if not deleted:
            response["msg"] = "Failed to delete cluster"
            return False, response
        return True, response


def update_cluster(provier_kwargs):
    raise NotImplementedError


def get_cluster(provider_kwargs, cluster={}):
    response = {}
    if provider_kwargs:
        if not cluster["id"] and not cluster["name"]:
            response["msg"] = "Either the id or name of the cluster must be provided"
            return False, response
        container_engine_client = new_cluster_engine_client(
            name=provider_kwargs["profile"]["name"]
        )
        if cluster["id"]:
            cluster_id = cluster["id"]
        else:
            cluster_object = oci_get_cluster_by_name(
                container_engine_client,
                provider_kwargs["profile"]["compartment_id"],
                cluster["name"],
            )
            cluster_id = cluster_object.id
        cluster_stack = oci_get_cluster_stack(
            container_engine_client,
            provider_kwargs["profile"]["compartment_id"],
            cluster_id,
        )
        response["cluster"] = to_dict(cluster_stack)
        return True, response
    return False, response
