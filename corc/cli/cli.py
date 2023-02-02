import argparse
import datetime
import json
from corc.defaults import (
    CORC_FUNCTIONS,
    CLUSTER,
    CLUSTER_NODE,
    CONFIG,
    JOB,
    JOB_META,
    PACKAGE_NAME,
    PROFILE,
    STORAGE,
    STORAGE_S3,
    VCN,
    VCN_SUBNET,
)
from corc.cli.parsers.job.job import (
    job_group,
    job_meta_group,
)
from corc.cli.parsers.providers.oci.cluster import cluster_identity_group
from corc.cli.parsers.cluster.cluster import (
    valid_cluster_group,
    cluster_schedule_group,
)
from corc.cli.input_groups.config import config_input_groups
from corc.cli.input_groups.providers.profile import profile_input_groups
from corc.cli.parsers.job.job import select_job_group
from corc.cli.parsers.storage.storage import (
    add_storage_group,
    delete_storage,
    download_storage,
    select_storage,
)
from corc.cli.parsers.storage.s3 import add_s3_group, s3_config_group, s3_extra
from corc.cli.helpers import cli_exec, import_from_module
from corc.util import eprint


def to_str(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()


def run():
    parser = argparse.ArgumentParser(prog=PACKAGE_NAME)
    commands = parser.add_subparsers(title="COMMAND")

    # Add corc functions to the CLI
    functions_cli(commands)

    # Instance
    # instance_parser = commands.add_parser("instance")
    # instance_cli(instance_parser)

    # Compute
    # compute_parser = commands.add_parser("compute")
    # compute_cli(compute_parser)

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


def functions_cli(commands):
    """
    Add the functions that corc supports to the CLI.
    """
    # Add corc functions
    for corc_function in CORC_FUNCTIONS:
        corc_function_name = corc_function.lower()

        function_provider = commands.add_parser(corc_function_name)
        function_commands = function_provider.add_subparsers(title="COMMAND")

        # Add a function provider
        add_function_parser = function_commands.add_parser(
            "add", help="add {} provider".format(corc_function_name)
        )
        add_provider_input_groups = import_from_module(
            "corc.cli.input_groups.{}".format(corc_function_name),
            "{}".format(corc_function_name),
            "add_provider_groups",
        )
        add_provider_groups, add_argument_groups = add_provider_input_groups(
            add_function_parser
        )

        add_function_parser.set_defaults(
            func=cli_exec,
            module_path="corc.orchestration.orchestrator",
            module_name="orchestrator",
            func_name="add_orchestration_provider",
            argument_groups=add_argument_groups,
        )

        # Remove a function provider
        remove_function_parser = function_commands.add_parser(
            "remove", help="remove {} provider".format(corc_function_name)
        )
        remove_provider_input_groups = import_from_module(
            "corc.cli.input_groups.{}".format(corc_function_name),
            "{}".format(corc_function_name),
            "remove_provider_groups",
        )
        remove_provider_groups, remove_argument_groups = remove_provider_input_groups(
            remove_function_parser
        )


# def compute_cli(parser):
#     compute_commands = parser.add_subparsers(title="COMMAND")

#     # TODO, maybe switch to COMPUTE_PROVIDERS
#     for provider in PROVIDERS:
#         # Provider commands
#         provider_compute_parser = compute_commands.add_parser(provider)
#         provider_compute_commands = provider_compute_parser.add_subparsers(
#             title="COMMAND"
#         )

#         run_parser = provider_compute_commands.add_parser("run")
#         job_meta_group(run_parser)
#         job_group(run_parser)
#         cluster_identity_group(run_parser)
#         cluster_schedule_group(run_parser)
#         select_storage(run_parser)
#         add_storage_group(run_parser)
#         s3_config_group(run_parser)
#         add_s3_group(run_parser)
#         run_parser.set_defaults(
#             func=cli_exec,
#             module_path="corc.providers.{provider}.job",
#             module_name="job",
#             func_name="run",
#             provider_groups=[PROFILE],
#             argument_groups=[CLUSTER, JOB_META, JOB, STORAGE_S3, STORAGE],
#         )

#         delete_job_parser = provider_compute_commands.add_parser("delete")
#         select_job_group(delete_job_parser)
#         cluster_identity_group(delete_job_parser)
#         delete_job_parser.set_defaults(
#             func=cli_exec,
#             module_path="corc.providers.{provider}.job",
#             module_name="job",
#             func_name="delete_job",
#             provider_groups=[PROFILE],
#             argument_groups=[CLUSTER, JOB_META, JOB],
#         )

#         list_parser = provider_compute_commands.add_parser("list")
#         job_meta_group(list_parser)
#         cluster_identity_group(list_parser)
#         list_parser.set_defaults(
#             func=cli_exec,
#             module_path="corc.providers.{provider}.job",
#             module_name="job",
#             func_name="list_job",
#         )

#         # result_parser = provider_compute_commands.add_parser("result")
#         # result_commands = result_parser.add_subparsers(title="COMMAND")

#         get_parser = provider_compute_commands.add_parser("get")
#         select_job_group(get_parser)
#         # results_group(get_parser)
#         select_storage(get_parser)
#         download_storage(get_parser)
#         s3_config_group(get_parser)
#         get_parser.set_defaults(
#             func=cli_exec,
#             module_path="corc.providers.{provider}.job",
#             module_name="job",
#             func_name="get_results",
#             argument_groups=[JOB_META, JOB, STORAGE_S3, STORAGE],
#         )

#         delete_parser = provider_compute_commands.add_parser("delete")
#         select_job_group(delete_parser)
#         # results_group(delete_parser)
#         select_storage(delete_parser)
#         s3_config_group(delete_parser)
#         delete_storage(delete_parser)
#         delete_parser.set_defaults(
#             func=cli_exec,
#             module_path="corc.providers.{provider}.job",
#             module_name="job",
#             func_name="delete_results",
#             argument_groups=[JOB_META, JOB, STORAGE_S3, STORAGE],
#         )

#         list_parser = provider_compute_commands.add_parser("list")
#         select_job_group(list_parser)
#         select_storage(list_parser)
#         s3_config_group(list_parser)
#         s3_extra(list_parser)
#         list_parser.set_defaults(
#             func=cli_exec,
#             module_path="corc.providers.{provider}.job",
#             module_name="job",
#             func_name="list_results",
#             argument_groups=[JOB_META, JOB, STORAGE_S3, STORAGE],
#         )


# def config_cli(parser):
#     config_commands = parser.add_subparsers(title="COMMAND")

#     for provider in PROVIDERS:
#         config_provider_parser = config_commands.add_parser(provider)
#         provider_commands = config_provider_parser.add_subparsers(title="COMMAND")
#         config_provider_generate_parser = provider_commands.add_parser("generate")

#         # Add the provider profile input arguments
#         _, _ = profile_input_groups(config_provider_generate_parser, provider)

#         # Allow the general config groups to be added
#         config_provider_groups, config_argument_groups = config_input_groups(
#             config_provider_generate_parser
#         )

#         config_provider_generate_parser.set_defaults(
#             func=cli_exec,
#             module_path="corc.cli.config",
#             module_name="config",
#             func_name="init_config",
#             provider_groups=config_provider_groups,
#             argument_groups=config_argument_groups,
#             skip_config_groups=[CONFIG],
#         )


# def cluster_cli(provider, parser):
#     cluster_commands = parser.add_subparsers(title="COMMAND")

#     # Start Command
#     start_parser = cluster_commands.add_parser("start")
#     start_cluster_groups = import_from_module(
#         "corc.cli.input_groups.providers.{}.cluster".format(provider),
#         "cluster",
#         "start_cluster_groups",
#     )
#     start_provider_groups, start_argument_groups = start_cluster_groups(start_parser)
#     start_parser.set_defaults(
#         func=cli_exec,
#         module_path="corc.cluster",
#         module_name="cluster",
#         func_name="start_cluster",
#         provider_groups=start_provider_groups,
#         argument_groups=start_argument_groups,
#     )

#     # Stop Command
#     stop_parser = cluster_commands.add_parser("stop")
#     stop_cluster_groups = import_from_module(
#         "corc.cli.input_groups.providers.{}.cluster".format(provider),
#         "cluster",
#         "stop_cluster_groups",
#     )
#     stop_provider_groups, stop_argument_groups = stop_cluster_groups(stop_parser)
#     stop_parser.set_defaults(
#         func=cli_exec,
#         module_path="corc.cluster",
#         module_name="cluster",
#         func_name="stop_cluster",
#         provider_groups=stop_provider_groups,
#         argument_groups=stop_argument_groups,
#     )

#     # Get Command
#     get_parser = cluster_commands.add_parser("get")
#     get_cluster_groups = import_from_module(
#         "corc.cli.input_groups.providers.{}.cluster".format(provider),
#         "cluster",
#         "get_cluster_groups",
#     )
#     get_provider_groups, get_argument_groups = get_cluster_groups(get_parser)
#     get_parser.set_defaults(
#         func=cli_exec,
#         module_path="corc.cluster",
#         module_name="cluster",
#         func_name="get_cluster",
#         provider_groups=get_provider_groups,
#         argument_groups=get_argument_groups,
#     )

#     # List Command
#     list_parser = cluster_commands.add_parser("list")
#     list_cluster_groups = import_from_module(
#         "corc.cli.input_groups.providers.{}.cluster".format(provider),
#         "cluster",
#         "list_cluster_groups",
#     )
#     list_provider_groups, list_argument_groups = list_cluster_groups(list_parser)
#     list_parser.set_defaults(
#         func=cli_exec,
#         module_path="corc.cluster",
#         module_name="cluster",
#         func_name="list_clusters",
#         provider_groups=list_provider_groups,
#         argument_groups=list_argument_groups,
#     )


# def instance_cli(parser):
#     instance_commands = parser.add_subparsers(title="COMMAND")
#     orchestration_parser = instance_commands.add_parser("orchestration")
#     orchestration_commands = orchestration_parser.add_subparsers(title="COMMAND")

#     # Add each provider type to the instance parsers
#     # Libvirt
#     for provider in PROVIDERS:
#         # Provider commands
#         provider_instance_parser = orchestration_commands.add_parser(provider)
#         provider_instance_commands = provider_instance_parser.add_subparsers(
#             title="COMMAND"
#         )

#         # Add the global provider
#         # global_provider_args = import_from_module
#         # TODO, simplify the import here, don't need the double abstraction
#         profile_input_groups(provider_instance_parser, provider)

#         # Start Command
#         start_parser = provider_instance_commands.add_parser("start")
#         start_instance_groups = import_from_module(
#             "corc.cli.input_groups.providers.{}.instance".format(provider),
#             "instance",
#             "start_instance_groups",
#         )
#         start_provider_groups, start_argument_groups = start_instance_groups(
#             start_parser
#         )

#         start_parser.set_defaults(
#             func=cli_exec,
#             module_path="corc.instance",
#             module_name="instance",
#             func_name="start_instance",
#             provider_groups=start_provider_groups,
#             argument_groups=start_argument_groups,
#         )

#         # Stop Command
#         stop_parser = provider_instance_commands.add_parser("stop")
#         stop_instance_groups = import_from_module(
#             "corc.cli.input_groups.providers.{}.instance".format(provider),
#             "instance",
#             "stop_instance_groups",
#         )
#         stop_provider_groups, stop_argument_groups = stop_instance_groups(stop_parser)
#         stop_parser.set_defaults(
#             func=cli_exec,
#             module_path="corc.instance",
#             module_name="instance",
#             func_name="stop_instance",
#             provider_groups=stop_provider_groups,
#             argument_groups=stop_argument_groups,
#         )

#         # Get Command
#         get_parser = provider_instance_commands.add_parser("get")
#         get_instance_groups = import_from_module(
#             "corc.cli.input_groups.providers.{}.instance".format(provider),
#             "instance",
#             "get_instance_groups",
#         )
#         (
#             get_provider_groups,
#             get_argument_groups,
#             get_none_config_groups,
#         ) = get_instance_groups(get_parser)
#         get_parser.set_defaults(
#             func=cli_exec,
#             module_path="corc.instance",
#             module_name="instance",
#             func_name="get_instance",
#             provider_groups=get_provider_groups,
#             argument_groups=get_argument_groups,
#             skip_config_groups=get_none_config_groups,
#         )

#         # List Command
#         list_parser = provider_instance_commands.add_parser("list")
#         list_instance_groups = import_from_module(
#             "corc.cli.input_groups.providers.{}.instance".format(provider),
#             "instance",
#             "list_instance_groups",
#         )
#         list_provider_groups, list_argument_groups = list_instance_groups(list_parser)
#         list_parser.set_defaults(
#             func=cli_exec,
#             module_path="corc.instance",
#             module_name="instance",
#             func_name="list_instances",
#             provider_groups=list_provider_groups,
#             argument_groups=list_argument_groups,
#         )


if __name__ == "__main__":
    arguments = run()
