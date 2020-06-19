from corc.cli.args import extract_arguments
from corc.defaults import OCI
from corc.config import (
    config_exists,
    load_config,
    save_config,
    generate_default_config,
    valid_config,
)
from corc.providers.oci.config import generate_oci_config, valid_oci_config


def init_config(args):
    oci_kwargs = vars(extract_arguments(args, [OCI]))
    oci_config_dict = {"oci": {"profile": oci_kwargs}}
    # Expects that the default corc config is present
    oci_config = generate_oci_config(**oci_config_dict)

    if not valid_oci_config(oci_config):
        raise ValueError("The generated oci config is invalid")

    # If no config exists -> create it
    config = {}
    if not config_exists():
        config = generate_default_config()
    else:
        config = load_config()

    if not config_exists():
        raise RuntimeError("Failed to find a config")

    # Update with user arguments
    config["corc"]["providers"].update(oci_config)

    if not save_config(config):
        raise RuntimeError("Failed to save new config")

    if not valid_config(config, verbose=True):
        raise ValueError("The generated config is invalid")
