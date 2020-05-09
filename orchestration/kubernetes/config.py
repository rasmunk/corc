import os
import yaml
from kubernetes import client, config
from kubernetes.config import ConfigException
from kubernetes.config.kube_config import KUBE_CONFIG_DEFAULT_LOCATION


def kube_config_loaded():
    try:
        config.load_kube_config()
        return True
    except (ConfigException, TypeError) as err:
        print("Failed to load kube config: {}".format(err))
    return False


def parse_yaml(data):
    try:
        parsed = yaml.safe_load(data)
        return parsed
    except yaml.reader.ReaderError as err:
        print("Failed to parse yaml: {}".format(err))
    return False


def save_kube_config(config_dict, config_file=None, user_exec_args=None):
    if not isinstance(config_dict, dict):
        return False
    if config_file is None:
        # Get the absolute path
        config_file = os.path.expanduser(KUBE_CONFIG_DEFAULT_LOCATION)
    with open(config_file, "w") as fh:
        yaml.dump(config_dict, fh)
    return True


def setup_config(
    container_engine_client, compartment_id, cluster_id, profile_name="DEFAULT"
):
    # Try to load the existing
    # Create or refresh the kubernetes config
    kube_config = create(container_engine_client, "create_kubeconfig", cluster_id)
    if kube_config and hasattr(kube_config, "text"):
        config_dict = parse_yaml(kube_config.text)
        # HACK, add profile to user args
        if profile_name:
            profile_args = ["--profile", profile_name]
            config_dict["users"][0]["user"]["exec"]["args"].extend(profile_args)
        if save_kube_config(config_dict):
            loaded = load_kube_config()

    loaded = load_kube_config()
    if not loaded:
        # The new/refreshed config failed to load
        return False
    return True
