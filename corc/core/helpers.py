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

import os
from corc.core.defaults import default_base_path


def is_in(a_values, b_struct):
    num_positives = 0
    a_len = len(a_values.keys())
    for k, v in a_values.items():
        if isinstance(b_struct, dict):
            if k in b_struct and b_struct[k] == v:
                num_positives += 1
        elif isinstance(b_struct, (list, set, tuple)):
            for b in b_struct:
                if b == v:
                    num_positives += 1
        else:
            if hasattr(b_struct, k):
                if getattr(b_struct, k) == v:
                    num_positives += 1
    if num_positives == a_len:
        return True
    return False


def exists_in_list(a_values, list_of_structs):
    for struct in list_of_structs:
        if is_in(a_values, struct):
            return True
    return False


def find_in_list(a_values, list_of_structs):
    for struct in list_of_structs:
        if is_in(a_values, struct):
            return struct
    return None


def exists_in_dict(a_values, dict_of_structs):
    for k, struct in dict_of_structs.items():
        if is_in(a_values, struct):
            return struct
    return None


def find_in_dict(a_values, dict_of_structs):
    for k, struct in dict_of_structs.items():
        if is_in(a_values, struct):
            return struct
    return None


def unset_check(value):
    if isinstance(value, str) and value == "":
        return True
    if isinstance(value, (bytes, bytearray)) and value == bytearray():
        return True
    if isinstance(value, list) and value == []:
        return True
    if isinstance(value, set) and value == set():
        return True
    if isinstance(value, tuple) and value == tuple():
        return True
    if isinstance(value, dict) and value == {}:
        return True
    if value is None:
        return True
    return False


def get_corc_path(path=None, env_postfix=None):
    if not path:
        path = default_base_path

    env_var = None
    if env_postfix and isinstance(env_postfix, str):
        env_var = "CORC_{}".format(env_postfix)
    if env_var in os.environ:
        path = os.environ[env_var]
    return path


def corc_home_path(path=None):
    return get_corc_path(path=path, env_postfix="HOME")


def import_from_module(module_path, module_name, func_name):
    module = __import__(module_path, fromlist=[module_name])
    return getattr(module, func_name)


def recursive_format(input, value):
    if isinstance(input, list):
        for item_index, item_value in enumerate(input):
            if isinstance(item_value, str):
                try:
                    input[item_index] = item_value.format(**value)
                except KeyError:
                    continue
            recursive_format(item_value, value)
    if isinstance(input, dict):
        for input_key, input_value in input.items():
            if isinstance(input_value, str):
                try:
                    input[input_key] = input_value.format(**value)
                except KeyError:
                    continue
            recursive_format(input_value, value)
    if hasattr(input, "__dict__"):
        recursive_format(input.__dict__, value)
