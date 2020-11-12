import os
from botocore.configloader import load_config
from botocore.credentials import SharedCredentialProvider
from corc.defaults import default_base_path


def is_in(a_values, b_struct):
    num_positives = 0
    a_len = len(a_values.keys())
    for k, v in a_values.items():
        if isinstance(b_struct, dict):
            if k in b_struct and b_struct[k] == v:
                num_positives += 1
        elif isinstance(b_struct, (list, set, tuple)):
            for b in b_struct:
                if b == v:
                    num_positives += 1
        else:
            if hasattr(b_struct, k):
                if getattr(b_struct, k) == v:
                    num_positives += 1
    if num_positives == a_len:
        return True
    return False


def exists_in_list(a_values, list_of_structs):
    for struct in list_of_structs:
        if is_in(a_values, struct):
            return True
    return False


def find_in_list(a_values, list_of_structs):
    for struct in list_of_structs:
        if is_in(a_values, struct):
            return struct
    return None


def exists_in_dict(a_values, dict_of_structs):
    for k, struct in dict_of_structs.items():
        if is_in(a_values, struct):
            return struct
    return None


def find_in_dict(a_values, dict_of_structs):
    for k, struct in dict_of_structs.items():
        if is_in(a_values, struct):
            return struct
    return None


def unset_check(value):
    if isinstance(value, str) and value == "":
        return True
    if isinstance(value, (bytes, bytearray)) and value == bytearray():
        return True
    if isinstance(value, list) and value == []:
        return True
    if isinstance(value, set) and value == set():
        return True
    if isinstance(value, tuple) and value == tuple():
        return True
    if isinstance(value, dict) and value == {}:
        return True
    if value is None:
        return True
    return False


def get_corc_path(path=default_base_path, env_postfix=None):
    env_var = None
    if env_postfix and isinstance(env_postfix, str):
        env_var = "CORC_{}".format(env_postfix)
    if env_var in os.environ:
        path = os.environ[env_var]
    return path


def corc_home_path(path=default_base_path):
    return get_corc_path(path=path, env_postfix="HOME")


def import_from_module(module_path, module_name, func_name):
    module = __import__(module_path, fromlist=[module_name])
    return getattr(module, func_name)


def load_aws_config(config_path, credentials_path, profile_name="default"):
    aws_config = load_config(config_path)
    if not aws_config:
        raise RuntimeError("Failed to load config: {}".format(config_path))

    aws_creds_provider = SharedCredentialProvider(
        credentials_path, profile_name=profile_name,
    )
    aws_creds_config = aws_creds_provider.load()
    if not aws_creds_config:
        raise RuntimeError(
            "Failed to load aws credentials config: {}".format(credentials_path)
        )
    (
        aws_access_key,
        aws_secret_key,
        aws_token,
    ) = aws_creds_config.get_frozen_credentials()

    profile_attributes = aws_config["profiles"][profile_name]
    aws_config = dict(
        aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key,
    )
    aws_config.update(profile_attributes)
    return aws_config
