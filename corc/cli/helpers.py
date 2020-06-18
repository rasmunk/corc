from corc.defaults import OCI
from corc.cli.job.job import (
    job_group,
    job_meta_group,
)
from corc.cli.cluster.cluster import (
    cluster_schedule_group,
    select_cluster_group,
    start_cluster_group,
)
from corc.cli.cluster.node import add_node_group
from corc.cli.config.config import add_config_group
from corc.cli.instance.instance import add_compute_group
from corc.cli.job.job import select_job_group
from corc.cli.job.result import results_group
from corc.cli.network.vcn import add_vcn_group
from corc.cli.network.subnet import add_subnet_group
from corc.cli.platform.oci import add_oci_group
from corc.cli.storage.storage import (
    add_storage_group,
    delete_storage,
    download_storage,
    select_storage,
)
from corc.cli.storage.s3 import add_s3_group, s3_config_group, s3_extra
from corc.cluster import list_clusters, start_cluster, stop_cluster, update_cluster
from corc.job import run, get_results, delete_results, list_results
from corc.instance import launch_instance


def job_cli(parser):
    job_commands = parser.add_subparsers(title="Commands")
    run_parser = job_commands.add_parser("run")
    job_meta_group(run_parser)
    job_group(run_parser)
    select_cluster_group(run_parser)
    cluster_schedule_group(run_parser)
    select_storage(run_parser)
    add_storage_group(run_parser)
    s3_config_group(run_parser)
    add_s3_group(run_parser)
    run_parser.set_defaults(func=run)

    result_parser = job_commands.add_parser("result")
    result_commands = result_parser.add_subparsers(title="Commands")

    get_parser = result_commands.add_parser("get")
    select_job_group(get_parser)
    results_group(get_parser)
    select_storage(get_parser)
    download_storage(get_parser)
    s3_config_group(get_parser)
    get_parser.set_defaults(func=get_results)

    delete_parser = result_commands.add_parser("delete")
    select_job_group(delete_parser)
    results_group(delete_parser)
    select_storage(delete_parser)
    s3_config_group(delete_parser)
    delete_storage(delete_parser)
    delete_parser.set_defaults(func=delete_results)

    list_parser = result_commands.add_parser("list")
    select_job_group(list_parser, required=False)
    select_storage(list_parser)
    s3_config_group(list_parser)
    s3_extra(list_parser)
    list_parser.set_defaults(func=list_results)


def add_config_cli(parser):
    config_commands = parser.add_subparsers(title="Commands")
    init_parser = config_commands.add_parser("init")
    add_config_group(init_parser)

    init_parser.set_defaults(func=)


def add_cluster_cli(parser):
    cluster_commands = parser.add_subparsers(title="Commands")
    start_parser = cluster_commands.add_parser("start")
    start_cluster_group(start_parser)
    add_node_group(start_parser)
    add_vcn_group(start_parser)
    add_subnet_group(start_parser)
    start_parser.set_defaults(func=start_cluster)

    stop_parser = cluster_commands.add_parser("stop")
    select_cluster_group(stop_parser)
    stop_parser.set_defaults(func=stop_cluster)

    list_parser = cluster_commands.add_parser("list")
    list_parser.set_defaults(func=list_clusters)

    update_parser = cluster_commands.add_parser("update")
    select_cluster_group(update_parser)
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
    platform_group.add_argument("platform", choices=[OCI], default=OCI)
    add_oci_group(parser)
