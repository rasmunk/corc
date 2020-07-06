from corc.providers.oci.cluster import (
    list_clusters as oci_list_clusters,
    delete_cluster_stack as oci_delete_cluster_stack,
    get_cluster_by_name as oci_get_cluster_by_name,
)
from corc.providers.oci.cluster import (
    OCIClusterOrchestrator,
    new_cluster_engine_client,
)


def list_clusters(provider_kwargs):
    if provider_kwargs:
        container_engine_client = new_cluster_engine_client(
            name=provider_kwargs["profile"]["name"]
        )
        return oci_list_clusters(
            container_engine_client, provider_kwargs["profile"]["compartment_id"]
        )


def start_cluster(provider_kwargs, cluster={}, vcn={}):
    # Interpolate general arguments with config
    if provider_kwargs:
        # Node shape is special
        if "shape" in cluster["node"]:
            cluster["node"]["node_shape"] = cluster["node"]["shape"]
            cluster["node"].pop("shape")

        # (Adapt) Split VCN and subnet
        subnet = vcn.pop("subnet")

        cluster_options = dict(
            oci=provider_kwargs, cluster=cluster, vcn=vcn, subnet=subnet,
        )
        OCIClusterOrchestrator.validate_options(cluster_options)
        orchestrator = OCIClusterOrchestrator(cluster_options)
        # TODO, poll if the cluster already exists
        orchestrator.setup()


def stop_cluster(provider_kwargs, cluster={}):
    if provider_kwargs:
        # Discover the vcn_stack for the cluster
        if not cluster["id"] and not cluster["name"]:
            raise ValueError("Either the id or name of the cluster must" "be provided")

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

        return oci_delete_cluster_stack(container_engine_client, cluster_id)


def update_cluster(provier_kwargs):
    raise NotImplementedError


def get_cluster(args):
    raise NotImplementedError
