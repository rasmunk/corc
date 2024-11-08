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

import asyncio


def strip_argument_prefix(arguments, prefix=""):
    return {k.replace(prefix, ""): v for k, v in arguments.items()}


def get_arguments(arguments, startswith=""):
    return {k: v for k, v in arguments.items() if k.startswith(startswith)}


def extract_arguments(arguments, argument_groups):
    found_kwargs, remaining_kwargs = {}, {}
    for argument_group in argument_groups:
        group_args = get_arguments(arguments, argument_group.lower())
        found_kwargs.update(group_args)
    remaining_kwargs = {
        k: v for k, v in arguments.items() if k not in found_kwargs and v
    }
    return found_kwargs, remaining_kwargs


def strip_argument_group_prefix(arguments, argument_groups):
    args = {}
    for argument_group in argument_groups:
        group_arguments = get_arguments(arguments, argument_group.lower())
        args.update(
            strip_argument_prefix(group_arguments, argument_group.lower() + "_")
        )
    return args


def get_argument_groups(arguments, groups=None):
    if not groups:
        groups = []

    args = []
    for group in groups:
        if group in arguments:
            args.append(getattr(arguments, group))
    return args


def import_from_module(module_path, module_name, func_name):
    module = __import__(module_path, fromlist=[module_name])
    return getattr(module, func_name)


def cli_exec(arguments):
    # Actions determines which function to execute
    module_path = arguments.pop("module_path")
    module_name = arguments.pop("module_name")
    func_name = arguments.pop("func_name")

    if "positional_arguments" in arguments:
        positional_arguments = arguments.pop("positional_arguments")
    else:
        positional_arguments = []

    if "argument_groups" in arguments:
        argument_groups = arguments.pop("argument_groups")
    else:
        argument_groups = []

    func = import_from_module(module_path, module_name, func_name)
    if not func:
        return False

    # Extract the arguments provided
    action_kwargs, remaining_action_kwargs = extract_arguments(
        arguments, argument_groups
    )
    action_kwargs = strip_argument_group_prefix(action_kwargs, argument_groups)
    if remaining_action_kwargs:
        print("Unused arguments: {}".format(remaining_action_kwargs))
    action_args = positional_arguments
    return asyncio.run(func(*action_args, **action_kwargs))
