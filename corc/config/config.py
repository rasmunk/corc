import os
import yaml
from corc.util import validate_dict_fields
from corc.config.defaults import valid_corc_config, default_config


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
