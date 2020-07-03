import argparse
import json
from corc.defaults import PACKAGE_NAME, AWS_LOWER, OCI_LOWER, PROFILE
from corc.defaults import CLUSTER, STORAGE, S3, JOB, JOB_META, NODE, VCN, SUBNET
from corc.cli.parsers.job.job import (
    job_group,
    job_meta_group,
)
from corc.cli.parsers.cluster.cluster import (
    cluster_schedule_group,
    select_cluster_group,
    start_cluster_group,
    valid_cluster_group,
)
from corc.cli.providers.oci import init_config
from corc.cli.parsers.config.config import add_config_group
from corc.cli.parsers.cluster.node import add_node_group
from corc.cli.parsers.instance.instance import add_compute_group
from corc.cli.parsers.job.job import select_job_group
from corc.cli.parsers.job.result import results_group
from corc.cli.parsers.network.vcn import add_vcn_group
from corc.cli.parsers.network.subnet import add_subnet_group
from corc.cli.parsers.storage.storage import (
    add_storage_group,
    delete_storage,
    download_storage,
    select_storage,
)
from corc.cli.parsers.storage.s3 import add_s3_group, s3_config_group, s3_extra
from corc.cli.parsers.providers.aws import add_aws_group
from corc.cli.parsers.providers.oci import add_oci_group
from corc.cluster import list_clusters, start_cluster, stop_cluster, update_cluster
from corc.job import get_results, delete_results, list_results
from corc.instance import launch_instance
from corc.cli.helpers import cli_exec


def run():
    parser = argparse.ArgumentParser(prog=PACKAGE_NAME)
    commands = parser.add_subparsers(title="COMMAND")
    config_parser = commands.add_parser("config")
    config_cli(config_parser)

    # AWS
    aws_parser = commands.add_parser(AWS_LOWER)
    add_aws_group(aws_parser)

    # OCI
    oci_parser = commands.add_parser(OCI_LOWER)
    add_oci_group(oci_parser)
    oci_commands = oci_parser.add_subparsers(title="COMMAND")
    orchestration_parser = oci_commands.add_parser("orchestration")
    orchestration_cli(orchestration_parser)

    job_parser = oci_commands.add_parser("job")
    job_cli(job_parser)

    args = parser.parse_args()
    # Execute default function
    if hasattr(args, "func"):
        result = args.func(args)
        if result:
            try:
                json_object = json.loads(result)
                print(json.dumps(json_object, indent=2))
            except Exception:
                print(result)
    return None


def job_cli(parser):
    job_commands = parser.add_subparsers(title="COMMAND")
    run_parser = job_commands.add_parser("run")
    job_meta_group(run_parser)
    job_group(run_parser)
    select_cluster_group(run_parser)
    cluster_schedule_group(run_parser)
    select_storage(run_parser)
    add_storage_group(run_parser)
    s3_config_group(run_parser)
    add_s3_group(run_parser)
    run_parser.set_defaults(
        func=cli_exec,
        module_path="corc.providers.{provider}.job",
        module_name="job",
        func_name="run",
        provider_groups=[PROFILE],
        argument_groups=[CLUSTER, JOB_META, JOB, STORAGE, S3],
    )

    result_parser = job_commands.add_parser("result")
    result_commands = result_parser.add_subparsers(title="COMMAND")

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
    select_job_group(list_parser)
    select_storage(list_parser)
    s3_config_group(list_parser)
    s3_extra(list_parser)
    list_parser.set_defaults(func=list_results)


def config_cli(parser):
    config_commands = parser.add_subparsers(title="COMMAND")
    # AWS
    aws_parser = config_commands.add_parser(AWS_LOWER)
    add_aws_group(aws_parser)
    # aws_commands = aws_parser.add_subparsers(title="COMMAND")
    # aws_init_parser = aws_commands.add_parser("init")

    # OCI
    oci_parser = config_commands.add_parser(OCI_LOWER)
    add_oci_group(oci_parser)
    oci_commands = oci_parser.add_subparsers(title="COMMAND")
    oci_generate_parser = oci_commands.add_parser("generate")
    add_config_group(oci_generate_parser)
    valid_cluster_group(oci_generate_parser)
    oci_generate_parser.set_defaults(func=init_config)


def cluster_cli(parser):
    cluster_commands = parser.add_subparsers(title="COMMAND")
    start_parser = cluster_commands.add_parser("start")
    start_cluster_group(start_parser)
    add_node_group(start_parser)
    add_vcn_group(start_parser)
    add_subnet_group(start_parser)
    start_parser.set_defaults(
        func=cli_exec,
        module_path="corc.cluster",
        module_name="cluster",
        func_name="start_cluster",
        provider_groups=[PROFILE],
        argument_groups=[CLUSTER, NODE, VCN, SUBNET],
    )

    stop_parser = cluster_commands.add_parser("stop")
    select_cluster_group(stop_parser)
    stop_parser.set_defaults(func=stop_cluster)

    list_parser = cluster_commands.add_parser("list")
    list_parser.set_defaults(func=list_clusters)

    update_parser = cluster_commands.add_parser("update")
    select_cluster_group(update_parser)
    update_parser.set_defaults(func=update_cluster)


def instance_cli(parser):
    instance_commands = parser.add_subparsers(title="COMMAND")
    launch_parser = instance_commands.add_parser("launch")
    add_compute_group(launch_parser)
    add_vcn_group(launch_parser)
    add_subnet_group(launch_parser)
    launch_parser.set_defaults(func=launch_instance)


def orchestration_cli(parser):
    orchestration_commands = parser.add_subparsers(title="COMMAND")
    oci_instance_parser = orchestration_commands.add_parser("instance")
    instance_cli(oci_instance_parser)
    oci_cluster_parser = orchestration_commands.add_parser("cluster")
    cluster_cli(oci_cluster_parser)


if __name__ == "__main__":
    arguments = run()
