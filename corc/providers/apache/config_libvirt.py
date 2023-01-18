import os
from corc.defaults import PROFILE, INSTANCE, LIBVIRT

default_config_path = os.path.join("~", ".libvirt", "config")

default_profile_config = {
    "name": "default",
    "config_file": default_config_path
}

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

libvirt_valid_config = {"profile": valid_profile_config, "instance": valid_instance_config}

libvirt_config_groups = {PROFILE: valid_profile_config, INSTANCE: valid_instance_config}


def load_driver_options(
    provider,
    provider_kwargs,
    config_path=default_config_path,
    profile_name="default",
    **kwargs
):

    hypervisor = None
    if "profile" in provider_kwargs:
        if "name" in provider_kwargs["profile"]:
            profile_name = provider_kwargs["profile"]["name"]

        if "hypervisor" in provider_kwargs["profile"]:
            hypervisor = provider_kwargs["profile"]["hypervisor"]

    libvirt_config = {}
    if "hypervisor" not in libvirt_config and hypervisor:
        libvirt_config["hypervisor"] = hypervisor

    return [], libvirt_config
