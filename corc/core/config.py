import copy
import flatten_dict
import os
from corc.utils.io import makedirs, exists, remove, dump_yaml, load_yaml
from corc.core.defaults import PACKAGE_NAME, default_base_path
from corc.core.helpers import get_corc_path
from corc.core.util import present_in, correct_type


default_config_path = os.path.join(default_base_path, "config")


def get_config_path(path=default_config_path):
    return get_corc_path(path=path, env_postfix="CONFIG_FILE")


def save_config(config, path=default_config_path):
    path = get_config_path(path)
    dir_path = os.path.dirname(path)
    if not exists(dir_path):
        created = makedirs(dir_path)
        if not created:
            print("Failed to create config directory: {}".format(dir_path))
            return False
    if not config:
        return False
    return dump_yaml(path, config)


def update_config(config, path=default_config_path):
    path = get_config_path(path)
    if not config:
        return False
    return dump_yaml(path, config, safe=True)


def load_config(path=default_config_path):
    path = get_config_path(path)
    if not os.path.exists(path):
        return False
    return load_yaml(path)


def config_exists(path=default_config_path):
    path = get_config_path(path)
    return exists(path)


def remove_config(path=default_config_path):
    path = get_config_path(path=path)
    if not os.path.exists(path):
        return True
    return remove(path)


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
    return gen_config_prefix(prefix=("providers",)) + provider


def gen_config_prefix(prefix=None):
    if prefix:
        return (PACKAGE_NAME,) + prefix
    return (PACKAGE_NAME,)
