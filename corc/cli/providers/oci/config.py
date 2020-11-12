from corc.providers.oci.config import generate_oci_config, valid_oci_config


def prepare_config(provider, provider_kwargs, cluster={}, vcn={}):
    config = {"oci": {"cluster": cluster}}
    config["oci"].update(provider_kwargs)

    # Expects that the default corc config is present
    config = generate_oci_config(**config)
    if not valid_oci_config(config, verbose=True):
        return False
    return config
