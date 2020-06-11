from corc.defaults import AWS, OCI
from corc.cli.args import (
    add_aws_group,
    add_compute_group,
    add_execute_group,
    add_job_meta_group,
    add_node_group,
    add_oci_group,
    add_subnet_group,
    add_storage_group,
    add_s3_group,
    add_vcn_group,
    start_cluster_group,
    stop_cluster_group,
    run_cluster_job_group,
)
from corc.cluster import list_clusters, start_cluster, stop_cluster, update_cluster
from corc.job import run
from corc.instance import launch_instance


def add_job_cli(parser):
    job_commands = parser.add_subparsers(title="Commands")
    run_parser = job_commands.add_parser("run")
    add_job_meta_group(run_parser)
    add_execute_group(run_parser)
    add_storage_group(run_parser)
    add_s3_group(run_parser)
    run_cluster_job_group(run_parser)
    run_parser.set_defaults(func=run)


def add_cluster_cli(parser):
    cluster_commands = parser.add_subparsers(title="Commands")
    start_parser = cluster_commands.add_parser("start")
    start_cluster_group(start_parser)
    add_node_group(start_parser)
    add_vcn_group(start_parser)
    add_subnet_group(start_parser)
    start_parser.set_defaults(func=start_cluster)

    stop_parser = cluster_commands.add_parser("stop")
    stop_cluster_group(stop_parser)
    stop_parser.set_defaults(func=stop_cluster)

    list_parser = cluster_commands.add_parser("list")
    list_parser.set_defaults(func=list_clusters)

    update_parser = cluster_commands.add_parser("update")
    # update_cluster_group(update_parser)
    update_parser.set_defaults(func=update_cluster)


def add_instance_cli(parser):
    instance_commands = parser.add_subparsers(title="Commands")
    launch_parser = instance_commands.add_parser("launch")
    add_compute_group(launch_parser)
    add_vcn_group(launch_parser)
    add_subnet_group(launch_parser)
    launch_parser.set_defaults(func=launch_instance)


def add_platform_group(parser):
    platform_group = parser.add_argument_group(title="Available Platforms")
    platform_group.add_argument("platform", choices=[OCI, AWS], default=OCI)
    add_oci_group(parser)
    add_aws_group(parser)
