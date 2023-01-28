import os
from corc.defaults import PROFILE, INSTANCE, LIBVIRT

default_config_path = os.path.join("~", ".libvirt", "config")

default_profile_config = {"name": "default", "config_file": default_config_path}

valid_profile_config = {"name": str, "config_file": str}

default_instance_config = {
    "name": "instance",
    "image": "",
    "size": "",
    "ssh_authorized_key": "",
}

valid_instance_config = {
    "name": str,
    "image": str,
    "size": str,
    "ssh_authorized_key": str,
}

default_config = {
    "profile": default_profile_config,
    "instance": default_instance_config,
}

libvirt_default_config = {LIBVIRT: default_config}

libvirt_valid_config = {
    "profile": valid_profile_config,
    "instance": valid_instance_config,
}

libvirt_config_groups = {PROFILE: valid_profile_config, INSTANCE: valid_instance_config}


def load_driver_options(
    provider,
    provider_kwargs,
    config_path=default_config_path,
    profile_name="default",
    **kwargs
):
    driver_args = []
    driver_kwargs = {}

    driver_uri = None
    driver_key = None
    driver_secret = None

    if "profile" in provider_kwargs:
        if "driver" in provider_kwargs["profile"]:
            provider_kwargs_driver = provider_kwargs["profile"]["driver"]
            if "uri" in provider_kwargs_driver:
                driver_uri = provider_kwargs_driver["uri"]

            if "key" in provider_kwargs_driver:
                driver_key = provider_kwargs_driver["key"]

            if "secret" in provider_kwargs_driver:
                driver_secret = provider_kwargs_driver["secret"]

    driver_args.append(driver_uri)
    driver_kwargs["key"] = driver_key
    driver_kwargs["secret"] = driver_secret

    return driver_args, driver_kwargs
