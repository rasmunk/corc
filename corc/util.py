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


def present_in(var, collection):
    if var not in collection:
        print("variable: {} not present in: {}".format(var, collection))
        return False
    return True


def validate_dict_types(input_dict, required_fields=None):
    if not required_fields:
        required_fields = {}
    for var, _type in required_fields.items():
        if not present_in(var, input_dict):
            return False
        if not isinstance(input_dict[var], _type):
            print(
                "variable: {} value: {} is of incorrect type: {}".format(
                    var, input_dict[var], type(input_dict[var])
                )
            )
            return False
    return True


def validate_dict_values(input_dict, required_values=None):
    if not required_values:
        required_values = {}

    for var, required_value in required_values.items():
        if not present_in(var, input_dict):
            return False
        if required_value and not input_dict[var]:
            print(
                "The required variable: {} was not set in: {}".format(var, input_dict)
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
