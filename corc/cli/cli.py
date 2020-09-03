import argparse
import datetime
import json
from corc.defaults import PACKAGE_NAME, AWS_LOWER, OCI_LOWER, PROFILE
from corc.defaults import (
    CLUSTER,
    CLUSTER_NODE,
    INSTANCE,
    JOB,
    JOB_META,
    STORAGE,
    STORAGE_S3,
    VCN,
    VCN_INTERNETGATEWAY,
    VCN_ROUTETABLE,
    VCN_SUBNET,
)
from corc.cli.parsers.job.job import (
    job_group,
    job_meta_group,
)
from corc.cli.parsers.cluster.cluster import (
    cluster_schedule_group,
    cluster_identity_group,
    cluster_node_group,
    start_cluster_group,
    valid_cluster_group,
)
from corc.cli.parsers.config.config import add_config_group
from corc.cli.parsers.instance.instance import (
    start_instance_group,
    instance_identity_group,
)
from corc.cli.parsers.job.job import select_job_group
from corc.cli.parsers.network.vcn import (
    vcn_identity_group,
    vcn_config_group,
    vcn_subnet_config_group,
)
from corc.cli.parsers.storage.storage import (
    add_storage_group,
    delete_storage,
    download_storage,
    select_storage,
)
from corc.cli.parsers.storage.s3 import add_s3_group, s3_config_group, s3_extra
from corc.cli.parsers.providers.aws import add_aws_group
from corc.cli.parsers.providers.oci import add_oci_group
from corc.cli.helpers import cli_exec
from corc.util import eprint


def to_str(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()


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
        success, response = args.func(args)
        output = ""
        if success:
            response["status"] = "success"
        else:
            response["status"] = "failed"

        try:
            output = json.dumps(response, indent=4, sort_keys=True, default=to_str)
        except Exception as err:
            eprint("Failed to format: {}, err: {}".format(output, err))
        if success:
            print(output)
        else:
            eprint(output)
    return None


def job_cli(parser):
    job_commands = parser.add_subparsers(title="COMMAND")
    run_parser = job_commands.add_parser("run")
    job_meta_group(run_parser)
    job_group(run_parser)
    cluster_identity_group(run_parser)
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
        argument_groups=[CLUSTER, JOB_META, JOB, STORAGE_S3, STORAGE],
    )

    delete_job_parser = job_commands.add_parser("delete")
    select_job_group(delete_job_parser)
    cluster_identity_group(delete_job_parser)
    delete_job_parser.set_defaults(
        func=cli_exec,
        module_path="corc.providers.{provider}.job",
        module_name="job",
        func_name="delete_job",
        provider_groups=[PROFILE],
        argument_groups=[CLUSTER, JOB_META, JOB],
    )

    list_parser = job_commands.add_parser("list")
    job_meta_group(list_parser)
    cluster_identity_group(list_parser)
    list_parser.set_defaults(
        func=cli_exec,
        module_path="corc.providers.{provider}.job",
        module_name="job",
        func_name="list_job",
    )

    result_parser = job_commands.add_parser("result")
    result_commands = result_parser.add_subparsers(title="COMMAND")

    get_parser = result_commands.add_parser("get")
    select_job_group(get_parser)
    # results_group(get_parser)
    select_storage(get_parser)
    download_storage(get_parser)
    s3_config_group(get_parser)
    get_parser.set_defaults(
        func=cli_exec,
        module_path="corc.providers.{provider}.job",
        module_name="job",
        func_name="get_results",
        argument_groups=[JOB_META, JOB, STORAGE_S3, STORAGE],
    )

    delete_parser = result_commands.add_parser("delete")
    select_job_group(delete_parser)
    # results_group(delete_parser)
    select_storage(delete_parser)
    s3_config_group(delete_parser)
    delete_storage(delete_parser)
    delete_parser.set_defaults(
        func=cli_exec,
        module_path="corc.providers.{provider}.job",
        module_name="job",
        func_name="delete_results",
        argument_groups=[JOB_META, JOB, STORAGE_S3, STORAGE],
    )

    list_parser = result_commands.add_parser("list")
    select_job_group(list_parser)
    select_storage(list_parser)
    s3_config_group(list_parser)
    s3_extra(list_parser)
    list_parser.set_defaults(
        func=cli_exec,
        module_path="corc.providers.{provider}.job",
        module_name="job",
        func_name="list_results",
        argument_groups=[JOB_META, JOB, STORAGE_S3, STORAGE],
    )


def config_cli(parser):
    config_commands = parser.add_subparsers(title="COMMAND")
    # AWS
    aws_parser = config_commands.add_parser(AWS_LOWER)
    add_aws_group(aws_parser)

    # OCI
    oci_parser = config_commands.add_parser(OCI_LOWER)
    add_oci_group(oci_parser)
    oci_commands = oci_parser.add_subparsers(title="COMMAND")
    oci_generate_parser = oci_commands.add_parser("generate")
    add_config_group(oci_generate_parser)
    valid_cluster_group(oci_generate_parser)
    oci_generate_parser.set_defaults(
        func=cli_exec,
        module_path="corc.cli.providers.{provider}",
        module_name="{provider}",
        func_name="init_config",
        provider_groups=[PROFILE],
        argument_groups=[CLUSTER_NODE, CLUSTER, VCN_SUBNET, VCN],
    )


def cluster_cli(parser):
    cluster_commands = parser.add_subparsers(title="COMMAND")
    start_parser = cluster_commands.add_parser("start")
    start_cluster_group(start_parser)
    cluster_identity_group(start_parser)
    cluster_node_group(start_parser)
    vcn_identity_group(start_parser)
    vcn_config_group(start_parser)
    vcn_subnet_config_group(start_parser)
    start_parser.set_defaults(
        func=cli_exec,
        module_path="corc.cluster",
        module_name="cluster",
        func_name="start_cluster",
        provider_groups=[PROFILE],
        argument_groups=[
            CLUSTER_NODE,
            CLUSTER,
            VCN_INTERNETGATEWAY,
            VCN_ROUTETABLE,
            VCN_SUBNET,
            VCN,
        ],
    )
    stop_parser = cluster_commands.add_parser("stop")
    cluster_identity_group(stop_parser)
    stop_parser.set_defaults(
        func=cli_exec,
        module_path="corc.cluster",
        module_name="cluster",
        func_name="stop_cluster",
        provider_groups=[PROFILE],
        argument_groups=[CLUSTER],
    )

    get_parser = cluster_commands.add_parser("get")
    cluster_identity_group(get_parser)
    get_parser.set_defaults(
        func=cli_exec,
        module_path="corc.cluster",
        module_name="cluster",
        func_name="get_cluster",
        provider_groups=[PROFILE],
        argument_groups=[CLUSTER],
    )

    list_parser = cluster_commands.add_parser("list")
    list_parser.set_defaults(
        func=cli_exec,
        module_path="corc.cluster",
        module_name="cluster",
        func_name="list_clusters",
        provider_groups=[PROFILE],
    )

    # update_parser = cluster_commands.add_parser("update")
    # cluster_identity_group(update_parser)
    # update_parser.set_defaults(func=update_cluster)


def instance_cli(parser):
    instance_commands = parser.add_subparsers(title="COMMAND")
    start_parser = instance_commands.add_parser("start")
    start_instance_group(start_parser)
    vcn_identity_group(start_parser)
    vcn_config_group(start_parser)
    start_parser.set_defaults(
        func=cli_exec,
        module_path="corc.instance",
        module_name="instance",
        func_name="start_instance",
        provider_groups=[PROFILE],
        argument_groups=[
            INSTANCE,
            VCN_INTERNETGATEWAY,
            VCN_ROUTETABLE,
            VCN_SUBNET,
            VCN,
        ],
    )

    stop_parser = instance_commands.add_parser("stop")
    instance_identity_group(stop_parser)
    stop_parser.set_defaults(
        func=cli_exec,
        module_path="corc.instance",
        module_name="instance",
        func_name="stop_instance",
        provider_groups=[PROFILE],
        argument_groups=[INSTANCE],
    )

    get_parser = instance_commands.add_parser("get")
    instance_identity_group(get_parser)
    get_parser.set_defaults(
        func=cli_exec,
        module_path="corc.instance",
        module_name="instance",
        func_name="get_instance",
        provider_groups=[PROFILE],
        argument_groups=[INSTANCE],
    )

    list_parser = instance_commands.add_parser("list")
    list_parser.set_defaults(
        func=cli_exec,
        module_path="corc.instance",
        module_name="instance",
        func_name="list_instances",
        provider_groups=[PROFILE],
    )


def orchestration_cli(parser):
    orchestration_commands = parser.add_subparsers(title="COMMAND")
    oci_instance_parser = orchestration_commands.add_parser("instance")
    instance_cli(oci_instance_parser)
    oci_cluster_parser = orchestration_commands.add_parser("cluster")
    cluster_cli(oci_cluster_parser)


if __name__ == "__main__":
    arguments = run()
