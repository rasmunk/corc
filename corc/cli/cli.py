import argparse
import datetime
import json
from corc.core.defaults import (
    CORC_CLI_STRUCTURE,
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
from corc.utils.format import eprint
from corc.core.plugins.plugin import get_plugins, import_plugin, PLUGIN_ENTRYPOINT_BASE
from corc.core.plugins.storage import load


def to_str(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()


def run():
    parser = argparse.ArgumentParser(prog=PACKAGE_NAME)
    commands = parser.add_subparsers(title="COMMAND")

    # Add corc functions to the CLI
    functions_cli(commands)
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


def recursive_add_corc_operations(
    corc_cli_type,
    corc_cli_operations,
    parser,
    module_core_prefix="corc.core",
    module_cli_prefix="corc.cli.input_groups",
):
    """This functions generates the corc cli interfaces for each operation type."""
    for operation in corc_cli_operations:
        if isinstance(operation, list):
            return recursive_add_corc_operations(corc_cli_type, operation, parser)
        if isinstance(operation, dict):
            # Note, we only expect there to be one key here
            operation_key = list(operation.keys())[0]
            # We postfix the module path with the
            # operation_key, such that loading will correctly occur once
            # we get down to an operation that is a simple string
            module_core_prefix = module_core_prefix + ".{}".format(operation_key)
            module_cli_prefix = module_cli_prefix + ".{}".format(operation_key)

            # Note, we expect the values to be a list that
            # contains the underlying operations
            operation_values = operation.values()
            operation_parser = parser.add_parser(operation_key)

            return recursive_add_corc_operations(
                corc_cli_type, operation_values, parser
            )
        # Dynamically import the different cli input groups
        if isinstance(operation, str):
            operation_parser = parser.add_parser(operation)
            operation_input_groups_func = import_from_module(
                "{}.{}".format(module_cli_prefix, corc_cli_type),
                "{}".format(corc_cli_type),
                "{}_groups".format(operation),
            )

            provider_groups = []
            argument_groups = []
            skip_groups = []
            input_groups = operation_input_groups_func(operation_parser)
            if not input_groups:
                raise RuntimeError(
                    "No input groups were returned by the input group function: {}".format(
                        operation_input_groups_func.func_name
                    )
                )

            if len(input_groups) == 3:
                provider_groups = input_groups[0]
                argument_groups = input_groups[1]
                skip_groups = input_groups[2]
            elif len(input_groups) == 2:
                provider_groups = input_groups[0]
                argument_groups = input_groups[1]
            else:
                # Only a single datatype was returned
                # and therefore should no longer be a tuple
                provider_groups = input_groups

            operation_parser.set_defaults(
                func=cli_exec,
                module_path="{}.{}.{}".format(
                    module_core_prefix, corc_cli_type, operation
                ),
                module_name="{}".format(corc_cli_type),
                func_name=operation,
                provider_groups=provider_groups,
                argument_groups=argument_groups,
                skip_groups=skip_groups,
            )


def functions_cli(commands):
    """
    Add the functions that corc supports to the CLI.
    """
    # Add the base corc CLI
    for corc_cli_structure in CORC_CLI_STRUCTURE:
        for corc_cli_type, corc_cli_operations in corc_cli_structure.items():
            function_provider = commands.add_parser(corc_cli_type)
            function_parser = function_provider.add_subparsers(title="COMMAND")
            recursive_add_corc_operations(
                corc_cli_type, corc_cli_operations, function_parser
            )
            # Load in the installed plugins and their CLIs
            plugin_entrypoint_type = "{}.{}".format(
                PLUGIN_ENTRYPOINT_BASE, corc_cli_type
            )
            type_plugins = get_plugins(plugin_type=plugin_entrypoint_type)
            for plugin in type_plugins:
                function_provider = function_parser.add_parser(plugin.name)
                function_cli_parser = function_provider.add_subparsers(title="COMMAND")
                cli_module_path = "{}.{}.{}".format(plugin.name, "cli", "cli")
                imported_cli_module = import_plugin(cli_module_path, return_module=True)
                if imported_cli_module:
                    imported_cli_module.functions_cli(function_cli_parser)


if __name__ == "__main__":
    arguments = run()
