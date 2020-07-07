from corc.config import (
    config_exists,
    load_config,
    save_config,
    generate_default_config,
    valid_config,
)
from corc.providers.oci.config import generate_oci_config, valid_oci_config


def init_config(provider_kwargs, cluster={}, vcn={}):
    oci_config_dict = {"oci": {"cluster": cluster}}
    oci_config_dict["oci"].update(provider_kwargs)

    # Expects that the default corc config is present
    oci_config = generate_oci_config(**oci_config_dict)
    response = {}
    if not valid_oci_config(oci_config, verbose=True):
        response["msg"] = "The generated oci config is invalid"
        return False, response

    # If no config exists -> create it
    config = {}
    if not config_exists():
        config = generate_default_config()
        save_config(config)
    else:
        config = load_config()

    if not config_exists():
        response["msg"] = "Failed to find a config"
        return False, response

    # Update with user arguments
    config["corc"]["providers"].update(oci_config)

    if not save_config(config):
        response["msg"] = "Failed to save new config"
        return False, response

    if not valid_config(config, verbose=True):
        response["msg"] = "The generated config is invalid"
        return False, response

    response["msg"] = "Generated a new configuration"
    return True, response
