import os
import yaml
from corc.defaults import ANSIBLE, AWS_LOWER, OCI_LOWER
from corc.providers.oci.config import valid_corc_config
from corc.util import validate_dict_fields

default_configurer_config = {}

valid_configurer_config = {
    "root_path": str,
    "playbook_path": str,
    "inventory_path": str,
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


default_config = {
    "corc": {
        "job": default_job_config,
        "storage": default_storage_config,
        "configurers": {ANSIBLE: default_configurer_config},
        "providers": {AWS_LOWER: {}, OCI_LOWER: {}, },
    }
}


def generate_default_config():
    return default_config


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


def valid_config(config, verbose=False, throw=False):
    if not isinstance(config, dict):
        return False

    for key, value in config.items():
        if key not in valid_corc_config:
            return False
        valid = validate_dict_fields(
            value, valid_corc_config[key], verbose=verbose, throw=throw
        )
        if not valid:
            return False

    return True
