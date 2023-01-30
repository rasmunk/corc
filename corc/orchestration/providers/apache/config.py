from corc.defaults import EC2, LIBVIRT
from corc.providers.ec2.config_ec2 import (
    ec2_config_groups,
    ec2_default_config,
    ec2_valid_config,
)
from corc.providers.libvirt.config_libvirt import (
    libvirt_config_groups,
    libvirt_default_config,
    libvirt_valid_config,
)


def load_config_groups(provider=None):
    if provider == EC2:
        return ec2_config_groups
    if provider == LIBVIRT:
        return libvirt_config_groups


def load_default_config(provider=None):
    if provider == EC2:
        return ec2_default_config
    if provider == LIBVIRT:
        return libvirt_default_config


def load_valid_config(provider=None):
    if provider == EC2:
        return ec2_valid_config
    if provider == LIBVIRT:
        return libvirt_valid_config
