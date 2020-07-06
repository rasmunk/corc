import copy
import flatten_dict
import os
import yaml
from corc.defaults import (
    ANSIBLE,
    AWS_LOWER,
    OCI_LOWER,
    PROVIDER,
    JOB,
    JOB_META,
    STORAGE,
    STORAGE_S3,
)
from corc.util import present_in, correct_type


default_configurer_config = {}

default_configurers_config = {ANSIBLE: default_configurer_config}

valid_configurer_config = {
    ANSIBLE: {"root_path": str, "playbook_path": str, "inventory_path": str,}
}

default_job_meta_config = {
    "name": "",
    "debug": False,
    "env_override": True,
    "num_jobs": 1,
    "num_parallel": 1,
}

valid_job_meta_config = {
    "name": str,
    "debug": bool,
    "env_override": bool,
    "num_jobs": int,
    "num_parallel": int,
}

default_job_config = {
    "meta": default_job_meta_config,
    "capture": True,
    "output_path": "/tmp/output",
}

valid_job_config = {
    "meta": dict,
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
    "name": "default",
    "bucket_id": "",
    "bucket_name": "",
    "bucket_input_prefix": "input",
    "bucket_output_prefix": "output",
}

valid_s3_config = {
    "config_file": str,
    "credentials_file": str,
    "name": str,
    "bucket_id": str,
    "bucket_name": str,
    "bucket_input_prefix": str,
    "bucket_output_prefix": str,
}

default_storage_config = {
    "enable": False,
    "s3": default_s3_storage_config,
    "endpoint": "",
    "credentials_path": "/mnt/creds",
    "upload_path": "",
    "input_path": "/tmp/input",
    "output_path": "/tmp/output",
    "download_path": "",
}


valid_storage_config = {
    "enable": bool,
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


corc_config_groups = {
    JOB: valid_job_config,
    JOB_META: valid_job_meta_config,
    STORAGE: valid_storage_config,
    STORAGE_S3: valid_s3_config,
    PROVIDER: valid_providers_config,
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


def load_from_env_or_config(find_dict={}, prefix=None, throw=False):
    value = False
    # Load from environment first
    dict_keys = flatten_dict.flatten(
        find_dict, reducer="underscore", keep_empty_types=(dict,)
    )
    list_keys = list(dict_keys.keys())
    if len(list_keys) > 1:
        return False
    env_var = list_keys[0].upper()

    value = load_from_env(env_var, throw=throw)
    if value:
        return value

    # Try config after
    if config_exists():
        config = load_config()
        if valid_config(config):
            values = load_from_config(find_dict, prefix=prefix)
            flat_values = list(flatten_dict.flatten(values).values())
            if flat_values and len(flat_values) == 1:
                value = flat_values[0]

    if throw and not value:
        raise ValueError(
            "Failed to find var: {} in either environment or config".format(prefix)
        )

    return value


def load_from_env(name, throw=False):
    if name in os.environ:
        return os.environ[name]
    if throw:
        raise ValueError("Missing required environment variable: {}".format(name))
    return False


def load_from_config(find_dict, prefix=None, config=None):
    if not find_dict or not config_exists():
        return {}

    if not config:
        config = load_config()
        if not config:
            return {}

    found_config_values = {}
    flat_find_dict = flatten_dict.flatten(find_dict, keep_empty_types=(dict,))
    flat_config = flatten_dict.flatten(config, keep_empty_types=(dict,))
    for k, _ in flat_find_dict.items():
        if prefix:
            prefixed_key = prefix + k
            if prefixed_key in flat_config:
                if (
                    isinstance(flat_config[prefixed_key], str)
                    and flat_config[prefixed_key]
                ):
                    found_config_values[k] = flat_config[prefixed_key]
                else:
                    found_config_values[k] = flat_config[prefixed_key]
        else:
            if k in flat_config and flat_config[k]:
                found_config_values[k] = flat_config[k]
    return flatten_dict.unflatten(found_config_values)


def gen_config_provider_prefix(provider):
    return gen_config_prefix(("providers",)) + provider


def gen_config_prefix(prefix):
    return ("corc",) + prefix