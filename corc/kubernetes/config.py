import os
from corc.util import dump_yaml
from kubernetes import config
from kubernetes.config import ConfigException
from kubernetes.config.kube_config import KUBE_CONFIG_DEFAULT_LOCATION


def load_kube_config():
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
    return dump_yaml(config_file, config_dict)
