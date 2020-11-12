import copy
import flatten_dict
import os
import yaml
from corc.defaults import (
    default_base_path,
    ANSIBLE,
    EC2,
    OCI_LOWER,
    PROVIDER,
    JOB,
    JOB_META,
    STORAGE,
    STORAGE_S3,
)
from corc.helpers import get_corc_path
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
    "working_dir": "",
}

valid_job_config = {
    "meta": dict,
    "commands": list,
    "capture": bool,
    "output_path": str,
    "working_dir": str,
}

default_providers_config = {EC2: {}, OCI_LOWER: {}}

valid_providers_config = {EC2: dict, OCI_LOWER: dict}


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
        "providers": {EC2: {}, OCI_LOWER: {},},
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

default_config_path = os.path.join(default_base_path, "config")


def generate_default_config():
    return default_corc_config


def get_config_path(path=default_config_path):
    return get_corc_path(path=path, env_postfix="CONFIG_FILE")


def save_config(config, path=default_config_path):
    path = get_config_path(path)
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


def update_config(config, path=default_config_path):
    path = get_config_path(path)
    if not config:
        return False

    try:
        with open(path, "w") as fh:
            yaml.safe_dump(config, fh)
    except Exception as err:
        print("Failed to save config: {}".format(err))
        return False
    return True


def load_config(path=default_config_path):
    path = get_config_path(path)
    if not os.path.exists(path):
        return False

    config = {}
    try:
        with open(path, "r") as fh:
            config = yaml.safe_load(fh)
    except Exception as err:
        print("Failed to load config: {}".format(err))
    return config


def config_exists(path=default_config_path):
    path = get_config_path(path)
    if not path:
        return False
    return os.path.exists(path)


def remove_config(path=default_config_path):
    path = get_config_path(path=path)
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


def load_from_env_or_config(
    find_dict={}, prefix=None, throw=False, path=default_config_path
):
    value = False
    # Load from environment first
    dict_keys = flatten_dict.flatten(
        find_dict, reducer="underscore", keep_empty_types=(dict,)
    )
    list_keys = list(dict_keys.keys())
    if len(list_keys) > 1:
        return False

    prefix_string = "_".join(prefix).upper()
    env_var = "{}_{}".format(prefix_string, list_keys[0].upper())
    env_error = None
    try:
        value = load_from_env(env_var, throw=throw)
    except ValueError as value_error:
        env_error = value_error

    if value:
        return value

    # Try config after
    if config_exists(path=path):
        config = load_config(path=path)
        if valid_config(config):
            values = load_from_config(find_dict, prefix=prefix, path=path)
            flat_values = list(flatten_dict.flatten(values).values())
            if flat_values and len(flat_values) == 1:
                value = flat_values[0]

    if throw:
        if env_error and not value:
            raise ValueError(
                "Failed to find var: {} in either environment or config, "
                "env_error: {}".format(prefix, env_error)
            )
    return value


def load_from_env(name, throw=False):
    if name in os.environ:
        return os.environ[name]
    if throw:
        raise ValueError("Missing required environment variable: {}".format(name))
    return False


def set_in_config(set_dict, prefix=None, path=default_config_path):
    if not prefix:
        prefix = tuple()

    config = load_config(path=path)
    if not config:
        return False

    flat_set_dict = flatten_dict.flatten(set_dict, keep_empty_types=(dict,))
    flat_config = flatten_dict.flatten(config, keep_empty_types=(dict,))
    for set_key, set_value in flat_set_dict.items():
        flat_config[prefix + set_key] = set_value

    unflatten_dict = flatten_dict.unflatten(flat_config)
    return update_config(unflatten_dict, path=path)


def load_from_config(
    find_dict, prefix=None, path=default_config_path, allow_sub_keys=False
):
    if not prefix:
        prefix = tuple()

    config = load_config(path=path)
    if not config:
        return {}

    found_config_values = {}
    flat_find_dict = flatten_dict.flatten(find_dict, keep_empty_types=(dict,))
    flat_config = flatten_dict.flatten(config, keep_empty_types=(dict,))
    for find_key, _ in flat_find_dict.items():
        for flat_key, flat_value in flat_config.items():
            prefixed_key = prefix + find_key
            intersection = tuple(
                [
                    v
                    for i, v in enumerate(prefixed_key)
                    if i < len(flat_key) and v == flat_key[i]
                ]
            )
            difference = tuple([v for v in flat_key if v not in intersection])
            # HACK, Only append differences at the current depth of the config,
            # e.g. don't allow subdict append
            if prefixed_key == intersection and (allow_sub_keys or not difference):
                sub_key = find_key + difference
                found_config_values[sub_key] = flat_value
    return flatten_dict.unflatten(found_config_values)


def gen_config_provider_prefix(provider):
    return gen_config_prefix(("providers",)) + provider


def gen_config_prefix(prefix):
    return ("corc",) + prefix
