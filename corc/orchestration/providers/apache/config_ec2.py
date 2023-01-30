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
    "image": "ami-0f18ced0fd6aae5c2",
    "size": "t1.micro",
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

    aws_access_key_id, aws_secret_access_key, region = None, None, None
    if "profile" in provider_kwargs:
        if "name" in provider_kwargs["profile"]:
            profile_name = provider_kwargs["profile"]["name"]

        if "config_file" in provider_kwargs["profile"]:
            config_path = os.path.expanduser(provider_kwargs["profile"]["config_file"])

        if "credentials_file" in provider_kwargs["profile"]:
            credentials_path = os.path.expanduser(
                provider_kwargs["profile"]["credentials_file"]
            )

        if "aws_access_key_id" in provider_kwargs["profile"]:
            aws_access_key_id = provider_kwargs["profile"]["aws_access_key_id"]

        if "aws_secret_access_key" in provider_kwargs["profile"]:
            aws_secret_access_key = provider_kwargs["profile"]["aws_secret_access_key"]

        if "region" in provider_kwargs["profile"]:
            region = provider_kwargs["profile"]["region"]

    config_exists = os.path.exists(config_path)
    credentials_exists = os.path.exists(credentials_path)

    aws_config = {}
    if config_exists and credentials_exists:
        aws_config = load_aws_config(
            config_path, credentials_path, profile_name=profile_name
        )

    if "region" not in aws_config and region:
        aws_config["region"] = region

    if not aws_access_key_id and config_exists:
        aws_access_key_id = aws_config.pop("aws_access_key_id")

    if not aws_secret_access_key and config_exists:
        aws_secret_access_key = aws_config.pop("aws_secret_access_key")

    return [aws_access_key_id, aws_secret_access_key], aws_config
