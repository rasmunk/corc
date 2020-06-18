from corc.cli.args import extract_arguments
from corc.defaults import CONFIG, OCI_LOWER
from corc.config import config_exists, load_config, save_config, generate_default_config
from corc.providers.oci.config import generate_oci_config


def init_config(args):
    config_kwargs = vars(extract_arguments(args, [CONFIG]))
    # Expects that the default corc config is present
    oci_config = generate_oci_config(**config_kwargs)

    # If no config exists -> create it
    config = {}
    if not config_exists():
        config = generate_default_config()
        save_config(config)
    else:
        config = load_config()

    if not config_exists():
        raise RuntimeError("Failed to find a config")

    config["corc"]["providers"][OCI_LOWER].update(oci_config)
    if not save_config(config):
        raise RuntimeError("Failed to save new config")
