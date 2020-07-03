from corc.defaults import OCI, CLUSTER, SUBNET, VCN, NODE
from corc.cli.args import extract_arguments
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


def start_cluster(provider_kwargs, cluster={}, node={}, vcn={}, subnet={}):
    # Interpolate general arguments with config
    if provider_kwargs:
        # Interpolate oci arguments with config
        # Validate oci authentication
        # Node shape is special
        if "shape" in node:
            node["node_shape"] = node["shape"]
            node.pop("shape")

        image_options = {}
        if "image" in node:
            image_name = node["image"]
            image_options = dict(display_name=image_name)
            node.pop("image")

        node["image"] = image_options

        cluster_options = dict(
            oci=provider_kwargs, cluster=cluster, node=node, vcn=vcn, subnet=subnet,
        )
        OCIClusterOrchestrator.validate_options(cluster_options)
        orchestrator = OCIClusterOrchestrator(cluster_options)
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
