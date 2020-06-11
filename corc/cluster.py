from corc.defaults import AWS, OCI, CLUSTER, SUBNET, VCN, NODE
from corc.cli.args import extract_arguments
from corc.oci.cluster import (
    list_clusters as oci_list_clusters,
    delete_cluster_stack as oci_delete_cluster_stack,
    get_cluster_by_name as oci_get_cluster_by_name,
)
from corc.oci.cluster import (
    OCIClusterOrchestrator,
    new_cluster_engine_client,
)


def list_clusters(args):
    oci_args = vars(extract_arguments(args, [OCI]))
    aws_args = vars(extract_arguments(args, [AWS]))

    if oci_args:
        container_engine_client = new_cluster_engine_client(
            profile_name=oci_args["profile_name"]
        )
        return oci_list_clusters(container_engine_client, oci_args["compartment_id"])

    if aws_args:
        pass


def start_cluster(args):
    oci_args = vars(extract_arguments(args, [OCI]))
    aws_args = vars(extract_arguments(args, [AWS]))
    cluster_args = vars(extract_arguments(args, [CLUSTER]))
    node_args = vars(extract_arguments(args, [NODE]))
    vcn_args = vars(extract_arguments(args, [VCN]))
    subnet_args = vars(extract_arguments(args, [SUBNET]))

    if oci_args:
        # Validate oci authentication
        # Node shape is special
        if "shape" in node_args:
            node_args["node_shape"] = node_args["shape"]
            node_args.pop("shape")

        image_options = {}
        if "image" in node_args:
            image_name = node_args["image"]
            image_options = dict(display_name=image_name)
            node_args.pop("image")

        node_args["image"] = image_options

        cluster_options = dict(
            oci=oci_args,
            cluster=cluster_args,
            node=node_args,
            vcn=vcn_args,
            subnet=subnet_args,
        )
        OCIClusterOrchestrator.validate_options(cluster_options)
        orchestrator = OCIClusterOrchestrator(cluster_options)
        orchestrator.setup()

    if aws_args:
        pass
        # return aws_run


def stop_cluster(args):
    oci_args = vars(extract_arguments(args, [OCI]))
    aws_args = vars(extract_arguments(args, [AWS]))
    cluster_args = vars(extract_arguments(args, [CLUSTER]))

    if oci_args:
        # Discover the vcn_stack for the cluster
        if not cluster_args["id"] and not cluster_args["name"]:
            raise ValueError("Either the id or name of the cluster must" "be provided")

        container_engine_client = new_cluster_engine_client(
            profile_name=oci_args["profile_name"]
        )
        if cluster_args["id"]:
            cluster_id = cluster_args["id"]
        else:
            cluster = oci_get_cluster_by_name(
                container_engine_client,
                oci_args["compartment_id"],
                cluster_args["name"],
            )
            cluster_id = cluster.id

        return oci_delete_cluster_stack(container_engine_client, cluster_id)

    if aws_args:
        pass


def update_cluster(args):
    oci_args = vars(extract_arguments(args, [OCI]))
    aws_args = vars(extract_arguments(args, [AWS]))
    # cluster_args = vars(extract_arguments(args, [CLUSTER]))
    # node_args = vars(extract_arguments(args, [NODE]))
    # vcn_args = vars(extract_arguments(args, [VCN]))
    # subnet_args = vars(extract_arguments(args, [SUBNET]))

    if oci_args:
        pass

    if aws_args:
        pass


def get_cluster(args):
    raise NotImplementedError
