import flatten_dict
import platform
import socket
import subprocess
import yaml


def parse_yaml(data):
    try:
        parsed = yaml.safe_load(data)
        return parsed
    except yaml.reader.ReaderError as err:
        print("Failed to parse yaml: {}".format(err))
    return False


def dump_yaml(path, data):
    try:
        with open(path, "w") as fh:
            yaml.dump(data, fh)
        return True
    except IOError as err:
        print("Failed to dump yaml: {} - {}".format(path, err))
    return False


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
        if not isinstance(value, (valid_fields[key],)):
            if verbose:
                print(
                    "variable: {}, value: {} is of incorrect type: {},"
                    " should be: {}".format(key, value, type(value), valid_fields[key])
                )
            if throw:
                raise TypeError(
                    "{}: should be {} but was: {}".format(
                        value, valid_fields[key], type(value)
                    )
                )
            return False
    return True


def validate_dict_types(input_dict, required_fields=None, verbose=False, throw=False):
    if not required_fields:
        required_fields = {}
    for var, _type in required_fields.items():
        if not present_in(var, input_dict, verbose=verbose):
            if throw:
                raise KeyError(
                    "Missing required: {} in {}".format(var, required_fields)
                )
            return False
        if not isinstance(input_dict[var], _type):
            if verbose:
                print(
                    "variable: {} value: {} is of incorrect type: {}".format(
                        var, input_dict[var], type(input_dict[var])
                    )
                )
            if throw:
                raise TypeError("{}: should be {}".format(var, _type))
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


def ping(host):
    """
    # https://stackoverflow.com/questions/2953462/pinging-servers-in-python
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP)
    request even if the host name is valid.
    """

    # Option for the number of packets as a function of
    param = "-n" if platform.system().lower() == "windows" else "-c"

    # Building the command. Ex: "ping -c 1 google.com"
    command = ["ping", param, "1", host]

    return subprocess.call(command) == 0


def open_port(host="127.0.0.1", port=22):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    if result == 0:
        return True
    else:
        return False
