import os
import yaml

from corc.config.defaults import default_config


def generate_config(config=None, path=None):
    if "CORC_CONFIG_FILE" in os.environ:
        path = os.environ["CORC_CONFIG_FILE"]
    else:
        if not path:
            path = os.path.join("~", ".corc", "config")

    if not config:
        config = default_config
    return config


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
        with open(path, 'r') as fh:
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


def valid_config(config):
    if not isinstance(config, dict):
        return False

    return True
