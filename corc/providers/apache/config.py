from corc.defaults import EC2
from corc.providers.ec2.config_ec2 import (
    ec2_config_groups,
    ec2_default_config,
    ec2_valid_config,
)


def load_config_groups(provider=None):
    if provider == EC2:
        return ec2_config_groups


def load_default_config(provider=None):
    if provider == EC2:
        return ec2_default_config


def load_valid_config(provider=None):
    if provider == EC2:
        return ec2_valid_config
