from corc.defaults import AWS, OCI
from corc.cli.args import (
    add_aws_group,
    add_cluster_group,
    add_compute_group,
    add_execute_group,
    add_job_meta_group,
    add_oci_group,
    add_subnet_group,
    add_storage_group,
    add_s3_group,
    add_vcn_group,
)
from corc.job import run
from corc.instance import launch_instance


def add_job_cli(parser):
    job_commands = parser.add_subparsers(title="Commands")
    run_parser = job_commands.add_parser("run")
    add_job_meta_group(run_parser)
    add_cluster_group(run_parser)
    add_execute_group(run_parser)
    add_storage_group(run_parser)
    add_s3_group(run_parser)
    run_parser.set_defaults(func=run)
    # stop_parser = job_commands.add_parser("stop")


def add_cluster_cli(parser):
    pass
    # cluster_commands = parser.add_subparsers(title="Commands")
    # start_parser = cluster_commands.add_parser("start")
    # terminate_parser = cluster_commands.add_parser("terminate")


def add_instance_cli(parser):
    instance_commands = parser.add_subparsers(title="Commands")
    launch_parser = instance_commands.add_parser("launch")
    add_compute_group(launch_parser)
    add_vcn_group(launch_parser)
    add_subnet_group(launch_parser)
    launch_parser.set_defaults(func=launch_instance)

    # command_group.add_argument('start')
    # instance_commands = parser.add_subparsers(title='COMMAND')
    # instance_commands.
    # start_parser = instance_commands.add_parser('start')
    # terminate_parser = instance_commands.add_parser('terminate')


def add_platform_group(parser):
    platform_group = parser.add_argument_group(title="Available Platforms")
    platform_group.add_argument("platform", choices=[OCI, AWS], default=OCI)
    add_oci_group(parser)
    add_aws_group(parser)
