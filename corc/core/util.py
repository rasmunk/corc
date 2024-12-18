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

from __future__ import print_function
import flatten_dict


def present_in(var, collection, verbose=False):
    if var not in collection:
        if verbose:
            print("variable: {} not present in: {}".format(var, collection))
        return False
    return True


def correct_type(var, required_type, verbose=False):
    if not isinstance(var, type):
        if verbose:
            print(
                "variable: {} is an incorrect type: {}, should be: {}".format(
                    var, type(var), required_type
                )
            )
        return False
    return True


def missing_fields(input_dict, required_fields, verbose=False, throw=False):
    missing = {}
    flat_input_fields = flatten_dict.flatten(input_dict)
    flat_required_fields = flatten_dict.flatten(required_fields)

    for k, v in flat_required_fields.items():
        # Not present or not set
        if not present_in(k, flat_input_fields) or not flat_input_fields[k]:
            missing[k] = None

    return flatten_dict.unflatten(missing)


def validate_dict_fields(input_dict, valid_fields, verbose=False, throw=False):
    for key, value in input_dict.items():
        if not present_in(key, valid_fields, verbose=verbose):
            if throw:
                raise KeyError(
                    "The key: {} is not allowed in: {}".format(key, valid_fields)
                )
            return False

        valid_value_types = valid_fields[key]
        if not isinstance(valid_value_types, (tuple, set)):
            valid_value_types = (valid_value_types,)

        valid = False
        if None in valid_value_types:
            if value is None:
                valid = True
            else:
                # Remove None from valid_value_types
                valid_value_types = tuple(
                    [v for v in valid_value_types if v is not None]
                )
        else:
            for valid_value_type in valid_value_types:
                if isinstance(value, valid_value_type):
                    valid = True

        if not valid:
            if verbose:
                print(
                    "variable: {}, value: {} is of incorrect type: {},"
                    " should be: {}".format(key, value, type(value), valid_value_types)
                )
            if throw:
                raise TypeError(
                    "{}: should be {} but was: {}".format(
                        value, valid_value_types, type(value)
                    )
                )
            return False
    return True


def validate_dict_values(input_dict, required_values=None, verbose=False, throw=False):
    if not required_values:
        required_values = {}

    for var, required_value in required_values.items():
        if not present_in(var, input_dict, verbose=verbose):
            if throw:
                raise KeyError("Missing required: {} in {} ".format(var, input_dict))
            return False
        if required_value and not input_dict[var]:
            if verbose:
                print(
                    "The required variable: {} was not set in: {}".format(
                        var, input_dict
                    )
                )
            if throw:
                raise ValueError(
                    "{} doesn't have a value: {}".format(var, required_value)
                )
            return False
    return True


def validate_either_values(input_dict, either_values, verbose=False, throw=False):
    """either values have to be present in input_dict"""
    valid = False
    is_set = {}
    for k, v in either_values.items():
        if k in input_dict and input_dict[k]:
            is_set[k] = True

    which_set = [k for k, v in is_set.items() if v]
    if not which_set:
        msg = "Neither: {} values were present in: {}".format(
            either_values.keys(), input_dict
        )
        if verbose:
            print(msg)
        if throw:
            raise ValueError(msg)
    elif len(which_set) > 1:
        msg = "Only one of: {} can be used, but: {} were set".format(
            either_values.keys(), which_set
        )
        if verbose:
            print(msg)
        if throw:
            raise ValueError(msg)
    else:
        valid = True
    return valid


def prepare_cls_kwargs(cls, **kwargs):
    cls_kwargs = {k: v for k, v in kwargs.items() if hasattr(cls, k)}
    return cls_kwargs


def has_method(object_, method):
    invert_op = getattr(object_, method, None)
    if callable(invert_op):
        return True
    return False
