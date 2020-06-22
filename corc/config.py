import copy
import os
import yaml
from corc.defaults import ANSIBLE, AWS_LOWER, OCI_LOWER
from corc.util import present_in, correct_type

default_configurer_config = {}

default_configurers_config = {ANSIBLE: default_configurer_config}

valid_configurer_config = {
    ANSIBLE: {"root_path": str, "playbook_path": str, "inventory_path": str,}
}

default_job_config = {
    "meta": {
        "name": "",
        "debug": False,
        "env_override": True,
        "num_jobs": 1,
        "num_parallel": 1,
    },
    "capture": True,
    "output_path": "/tmp/output",
}

valid_job_config = {
    "meta": {
        "name": str,
        "debug": bool,
        "env_override": bool,
        "num_jobs": int,
        "num_parallel": int,
    },
    "command": str,
    "args": list,
    "capture": bool,
    "output_path": str,
}

default_providers_config = {AWS_LOWER: {}, OCI_LOWER: {}}

valid_providers_config = {AWS_LOWER: dict, OCI_LOWER: dict}


default_s3_storage_config = {
    "config_file": "~/.aws/config",
    "credentials_file": "~/.aws/credentials",
    "profile_name": "default",
    "bucket_id": "",
    "bucket_name": "",
    "bucket_input_prefix": "input",
    "bucket_output_prefix": "output",
}

valid_s3_config = {
    "config_file": str,
    "credentials_file": str,
    "profile_name": str,
    "bucket_id": str,
    "bucket_name": str,
    "bucket_input_prefix": str,
    "bucket_output_prefix": str,
}

default_storage_config = {
    "s3": default_s3_storage_config,
    "endpoint": "",
    "credentials_path": "/mnt/creds",
    "upload_path": "",
    "input_path": "/tmp/input",
    "output_path": "/tmp/output",
    "download_path": "",
}


valid_storage_config = {
    "s3": dict,
    "endpoint": str,
    "credentials_path": str,
    "upload_path": str,
    "input_path": str,
    "output_path": str,
    "download_path": str,
}


default_corc_config = {
    "corc": {
        "job": default_job_config,
        "storage": default_storage_config,
        "configurers": {ANSIBLE: default_configurer_config},
        "providers": {AWS_LOWER: {}, OCI_LOWER: {},},
    }
}

valid_corc_config = {
    "job": valid_job_config,
    "storage": valid_storage_config,
    "configurers": valid_configurer_config,
    "providers": valid_providers_config,
}


def generate_default_config():
    return default_corc_config


def save_config(config, path=None):
    if "CORC_CONFIG_FILE" in os.environ:
        path = os.environ["CORC_CONFIG_FILE"]
    else:
        if not path:
            # Ensure the directory path is there
            path = os.path.join(os.path.expanduser("~"), ".corc", "config")
            dir_path = os.path.dirname(path)
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(os.path.dirname(path))
                except Exception as err:
                    print("Failed to create config directory: {}".format(err))

    if not config:
        return False

    try:
        with open(path, "w") as fh:
            yaml.safe_dump(config, fh)
    except Exception as err:
        print("Failed to save config: {}".format(err))
        return False
    return True


def update_config(config, path=None):
    if "CORC_CONFIG_FILE" in os.environ:
        path = os.environ["CORC_CONFIG_FILE"]
    else:
        if not path:
            # Ensure the directory path is there
            path = os.path.join(os.path.expanduser("~"), ".corc", "config")

    if not os.path.exists(path):
        raise Exception("Trying to update a config that doesn't exist")

    if not config:
        return False

    # Load config
    existing_config = load_config(path=path)
    if not existing_config:
        return False

    try:
        with open(path, "w") as fh:
            yaml.safe_dump(config, fh)
    except Exception as err:
        print("Failed to save config: {}".format(err))
        return False
    return True


def load_config(path=None):
    config = {}
    if "CORC_CONFIG_FILE" in os.environ:
        path = os.environ["CORC_CONFIG_FILE"]
    else:
        if not path:
            path = os.path.join(os.path.expanduser("~"), ".corc", "config")

    if not os.path.exists(path):
        return False
    try:
        with open(path, "r") as fh:
            config = yaml.safe_load(fh)
    except Exception as err:
        print("Failed to load config: {}".format(err))
    return config


def config_exists(path=None):
    if "CORC_CONFIG_FILE" in os.environ:
        path = os.environ["CORC_CONFIG_FILE"]
    else:
        if not path:
            path = os.path.join(os.path.expanduser("~"), ".corc", "config")

    if not path:
        return False

    return os.path.exists(path)


def remove_config(path=None):
    if "CORC_CONFIG_FILE" in os.environ:
        path = os.environ["CORC_CONFIG_FILE"]
    else:
        if not path:
            path = os.path.join(os.path.expanduser("~"), ".corc", "config")

    if not os.path.exists(path):
        return True
    try:
        os.remove(path)
    except Exception as err:
        print("Failed to remove config: {}".format(err))
        return False
    return True


def recursive_check_config(
    config, valid_dict, remain_config=None, remain_valid=None, verbose=False
):

    local_config = copy.deepcopy(config)

    while local_config.items():
        key, value = local_config.popitem()
        if not remain_config:
            remain_config = copy.deepcopy(local_config)
        if key in remain_config:
            remain_config.pop(key)
        if not remain_valid:
            remain_valid = valid_dict

        # Illegal key
        if not present_in(key, valid_dict, verbose=verbose):
            return False

        if isinstance(value, dict) and isinstance(valid_dict[key], dict):
            return recursive_check_config(
                value,
                valid_dict[key],
                remain_config=remain_config,
                remain_valid=remain_valid,
                verbose=verbose,
            )

        if not correct_type(type(value), valid_dict[key], verbose=verbose):
            return False

    if remain_config and remain_config.items():
        return recursive_check_config(remain_config, remain_valid, verbose=verbose)

    return True


def valid_config(config, verbose=False):
    if not isinstance(config, dict):
        return False

    if "corc" not in config:
        return False

    return recursive_check_config(config["corc"], valid_corc_config, verbose=verbose)
