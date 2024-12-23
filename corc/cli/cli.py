# Copyright (C) 2024  rasmunk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import argparse
import datetime
import json
import sys
from corc.core.defaults import PACKAGE_NAME, CORC_CLI_STRUCTURE
from corc.cli.helpers import cli_exec, import_from_module
from corc.utils.format import error_print
from corc.core.plugins.plugin import (
    get_plugins,
    import_plugin,
    PLUGIN_ENTRYPOINT_BASE,
    get_plugin_module_path_and_func,
)

from corc.cli.return_codes import SUCCESS, FAILURE


def to_str(o):
    if hasattr(o, "asdict"):
        return o.asdict()
    if isinstance(o, datetime.datetime):
        return o.__str__()


def main(args=None):
    parser = argparse.ArgumentParser(
        prog=PACKAGE_NAME, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    commands = parser.add_subparsers(title="COMMAND")

    # Add corc functions to the CLI
    cli(commands)
    parsed_args = parser.parse_args(args)
    # Convert to a dictionary
    arguments = vars(parsed_args)
    # Execute default function
    if "func" in arguments:
        func = arguments.pop("func")
        success, response = func(arguments)
        output = ""
        if success:
            response["status"] = "success"
        else:
            response["status"] = "failed"

        try:
            output = json.dumps(response, indent=4, sort_keys=True, default=to_str)
        except Exception as err:
            error_print("Failed to format: {}, err: {}".format(output, err))
            return FAILURE
        if success:
            print(output)
            return SUCCESS
        else:
            error_print(output)
            return FAILURE
    return SUCCESS


def recursive_add_corc_operations(
    corc_cli_type,
    corc_cli_operations,
    parser,
    module_core_prefix="corc.core",
    module_cli_prefix="corc.cli.input_groups",
):
    """This functions generates the corc cli interfaces for each operation type."""
    if isinstance(corc_cli_operations, list):
        for operation in corc_cli_operations:
            recursive_add_corc_operations(
                corc_cli_type,
                operation,
                parser,
                module_core_prefix=module_core_prefix,
                module_cli_prefix=module_cli_prefix,
            )
    elif isinstance(corc_cli_operations, dict):
        for operation_key, operation in corc_cli_operations.items():
            # We postfix the module path with the
            # operation_key, such that loading will correctly occur once
            # we get down to an operation that is a simple string
            module_core_prefix = "{}.{}".format(module_core_prefix, operation_key)
            module_cli_prefix = "{}.{}".format(module_cli_prefix, operation_key)

            # Note, we expect the values to be a list that
            # contains the underlying operations
            # operation_cli_type = "{}.{}".format(corc_cli_type, operation_key)
            operation_parser = parser.add_parser(operation_key)
            operation_subparser = operation_parser.add_subparsers(title="COMMAND")

            return recursive_add_corc_operations(
                operation_key,
                operation,
                operation_subparser,
                module_core_prefix=module_core_prefix,
                module_cli_prefix=module_cli_prefix,
            )
    # Dynamically import the different cli input groups
    elif isinstance(corc_cli_operations, str):
        add_corc_cli_operation(
            corc_cli_type,
            corc_cli_operations,
            parser,
            module_core_prefix=module_core_prefix,
            module_cli_prefix=module_cli_prefix,
        )


def add_corc_cli_operation(
    corc_cli_type,
    operation,
    parser,
    module_core_prefix="corc.core",
    module_cli_prefix="corc.cli.input_groups",
):
    operation_parser = parser.add_parser(operation)
    operation_input_groups_func = import_from_module(
        "{}.{}".format(module_cli_prefix, corc_cli_type),
        "{}".format(operation),
        "{}_groups".format(operation),
    )

    provider_groups = []
    argument_groups = []
    input_groups = operation_input_groups_func(operation_parser)
    if not input_groups:
        raise RuntimeError(
            "No input groups were returned by the input group function: {}".format(
                operation_input_groups_func.func_name
            )
        )

    if len(input_groups) == 2:
        provider_groups = input_groups[0]
        argument_groups = input_groups[1]
    else:
        # Only a single datatype was returned
        # and therefore should no longer be a tuple
        provider_groups = input_groups

    operation_parser.set_defaults(
        func=cli_exec,
        module_path="{}.{}".format(module_core_prefix, operation),
        module_name="{}".format(operation),
        func_name=operation,
        provider_groups=provider_groups,
        argument_groups=argument_groups,
    )


def cli(commands):
    """
    Add the functions that corc supports to the CLI.
    """
    # Add the base corc CLI
    for corc_cli_structure in CORC_CLI_STRUCTURE:
        for corc_cli_type, corc_cli_operations in corc_cli_structure.items():
            function_provider = commands.add_parser(corc_cli_type)
            function_parser = function_provider.add_subparsers(title="COMMAND")
            recursive_add_corc_operations(
                corc_cli_type,
                corc_cli_operations,
                function_parser,
                module_core_prefix="{}.core.{}".format(PACKAGE_NAME, corc_cli_type),
                module_cli_prefix="{}.cli.input_groups.{}".format(
                    PACKAGE_NAME, corc_cli_type
                ),
            )
            # Load in the installed plugins and their CLIs
            plugin_entrypoint_type = "{}.{}".format(
                PLUGIN_ENTRYPOINT_BASE, corc_cli_type
            )
            type_plugins = get_plugins(plugin_type=plugin_entrypoint_type)
            for plugin in type_plugins:
                function_provider = function_parser.add_parser(plugin.name)
                function_cli_parser = function_provider.add_subparsers(title="COMMAND")
                cli_module_path, cli_module_function_name = (
                    get_plugin_module_path_and_func(
                        plugin.name,
                        plugin_module_entrypoint="{}.cli".format(
                            PLUGIN_ENTRYPOINT_BASE
                        ),
                    )
                )
                if cli_module_path and cli_module_function_name:
                    imported_cli_module = import_plugin(
                        cli_module_path, return_module=True
                    )
                    if imported_cli_module:
                        plugin_cli_function = getattr(
                            imported_cli_module, cli_module_function_name
                        )
                        plugin_cli_function(function_cli_parser)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
