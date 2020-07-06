import os
from corc.util import dump_yaml, create_directory
from kubernetes import config
from kubernetes.config import ConfigException
from kubernetes.config.kube_config import KUBE_CONFIG_DEFAULT_LOCATION


def load_kube_config():
    config_file = os.path.expanduser(KUBE_CONFIG_DEFAULT_LOCATION)
    if not os.path.exists(config_file):
        print("The kube config file doesn't exist")
        return False

    try:
        config.load_kube_config()
        return True
    except (ConfigException, TypeError) as err:
        print("Failed to load kube config: {}".format(err))
    return False


def save_kube_config(config_dict, config_file=None, user_exec_args=None):
    if not isinstance(config_dict, dict):
        return False
    if config_file is None:
        # Get the absolute path
        config_file = os.path.expanduser(KUBE_CONFIG_DEFAULT_LOCATION)

    # Ensure the directory path exists before dump
    if not create_directory(os.path.dirname(config_file)):
        return False

    return dump_yaml(config_file, config_dict)
