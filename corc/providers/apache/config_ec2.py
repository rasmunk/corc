import os
from corc.defaults import PROFILE, INSTANCE
from corc.helpers import load_aws_config

default_config_path = os.path.join("~", ".aws", "config")
default_credentials_path = os.path.join("~", ".aws", "credentials")

default_profile_config = {
    "name": "default",
    "config_file": default_config_path,
    "credentials_file": default_credentials_path,
}

valid_profile_config = {"name": str, "config_file": str, "credentials_file": str}

default_instance_config = {
    "name": "instance",
    "image": "ami-01ca03df4a6012157",
    "size": "t1.micro",
}

valid_instance_config = {"name": str, "image": str, "size": str}

default_config = {
    "profile": default_profile_config,
    "instance": default_instance_config,
}

ec2_default_config = {"ec2": default_config}

ec2_valid_config = {"profile": valid_profile_config, "instance": valid_instance_config}

ec2_config_groups = {PROFILE: valid_profile_config, INSTANCE: valid_instance_config}


def load_driver_options(
    provider,
    provider_kwargs,
    config_path=default_config_path,
    credentials_path=default_credentials_path,
    profile_name="default",
    **kwargs
):
    if "profile" in provider_kwargs:
        if "name" in provider_kwargs["profile"]:
            profile_name = provider_kwargs["profile"]["name"]

        if "config_file" in provider_kwargs["profile"]:
            config_path = provider_kwargs["profile"]["config_file"]

        if "credentials_file" in provider_kwargs["profile"]:
            credentials_path = provider_kwargs["profile"]["credentials_file"]

    if "{}_CONFIG_PATH".format(provider) in os.environ:
        config_path = os.environ["{}_CONFIG_PATH".format(provider)]

    if "{}_CREDENTIALS_PATH".format(provider) in os.environ:
        credentials_path = os.environ["{}_CREDENTIALS_PATH".format(provider)]

    if "{}_PROFILE_NAME".format(provider) in os.environ:
        profile_name = os.environ["{}_PROFILE_NAME".format(provider)]

    aws_config = load_aws_config(
        config_path, credentials_path, profile_name=profile_name
    )
    aws_access_key_id = aws_config.pop("aws_access_key_id")
    aws_secret_access_key = aws_config.pop("aws_secret_access_key")

    return [aws_access_key_id, aws_secret_access_key], aws_config
