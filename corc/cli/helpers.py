from argparse import Namespace
import copy
import flatten_dict
from corc.cli.args import extract_arguments, wrap_extract_arguments
from corc.cli.providers.helpers import select_provider
from corc.config import (
    load_from_config,
    corc_config_groups,
    gen_config_prefix,
    gen_config_provider_prefix,
)
from corc.helpers import import_from_module
from corc.defaults import PROVIDERS_LOWER
from corc.util import missing_fields
from corc.providers.config import get_provider_config_groups


def cli_exec(args):
    # action determines which function to execute
    module_path = args.module_path
    module_name = args.module_name
    func_name = args.func_name
    if hasattr(args, "provider_groups"):
        provider_groups = args.provider_groups
    else:
        provider_groups = []

    if hasattr(args, "argument_groups"):
        argument_groups = args.argument_groups
    else:
        argument_groups = []

    if hasattr(args, "skip_config_groups"):
        skip_config_groups = args.skip_config_groups
    else:
        skip_config_groups = []

    provider, provider_kwargs = prepare_provider_kwargs(args, namespace_wrap=True)
    if provider:
        module_path = module_path.format(provider=provider)
        # load missing provider kwargs from config
        provider_configuration = prepare_kwargs_configurations(
            provider, provider_kwargs, provider_groups, strip_group_prefix=False
        )
        provider_kwargs = load_missing_action_kwargs(provider_configuration)

    func = import_from_module(module_path, module_name, func_name)
    if not func:
        return False

    # Extract config kwargs from args
    kwargs_configuration = prepare_kwargs_configurations(
        provider, args, argument_groups
    )
    # Load config and fill in missing values
    action_kwargs = load_missing_action_kwargs(kwargs_configuration)

    # Extract none config kwargs from args
    extra_action_kwargs = prepare_none_config_kwargs(args, skip_config_groups)

    if provider:
        return func(provider, provider_kwargs, **action_kwargs, **extra_action_kwargs)
    return func(**action_kwargs, **extra_action_kwargs)


def prepare_none_config_kwargs(args, skip_config_groups_groups):
    kwargs = wrap_extract_arguments(args, skip_config_groups_groups)
    return kwargs


def prepare_provider_kwargs(args, namespace_wrap=False):
    providers = vars(extract_arguments(args, PROVIDERS_LOWER, strip_group_prefix=False))
    provider = select_provider(providers, default_fallback=True, verbose=True)
    provider_kwargs = vars(extract_arguments(args, [provider]))
    # remove the provider flag
    provider_kwargs.pop(provider)
    if namespace_wrap:
        provider_kwargs = Namespace(**provider_kwargs)
    return provider, provider_kwargs


def prepare_kwargs_configurations(
    provider, args, argument_groups, strip_group_prefix=True
):
    """ Used to load missing arguments from the configuration file """
    # Try to find all available args
    kwargs_configurations = []
    for group in argument_groups:
        group_kwargs_config = {}
        name = group.lower()
        # Flat group_kwargs_config to do direct indexing
        if "_" in name:
            prefix = tuple(name.split("_"))
            group_kwargs_config = create_sub_dictionaries(group_kwargs_config, prefix)
        else:
            prefix = (name,)
            group_kwargs_config[name] = {}

        prefix_action_kwargs = prefix + ("action_kwargs",)
        prefix_action_config = prefix + ("valid_action_config",)
        prefix_config_prefix = prefix + ("config_prefix",)

        flat_group_kwargs_config = flatten_dict.flatten(
            group_kwargs_config, keep_empty_types=(dict,)
        )
        # TODO, subname on split prefix
        action_kwargs = vars(extract_arguments(args, [group]))
        if action_kwargs:
            # remove claimed action_kwargs from args
            args = remove_arguments(args, action_kwargs.keys(), prefix=name + "_")
            flat_group_kwargs_config[prefix_action_kwargs] = action_kwargs
        else:
            flat_group_kwargs_config[prefix_action_kwargs] = {}

        if group in corc_config_groups:
            valid_action_config = corc_config_groups[group]
            # gen config prefix
            config_prefix = gen_config_prefix(prefix)
            flat_group_kwargs_config[prefix_action_config] = valid_action_config
            flat_group_kwargs_config[prefix_config_prefix] = config_prefix

        provider_groups = get_provider_config_groups(provider)
        if group in provider_groups:
            valid_action_config = provider_groups[group]
            prefix = (provider,) + prefix
            config_prefix = gen_config_provider_prefix(prefix)
            flat_group_kwargs_config[prefix_action_config] = valid_action_config
            flat_group_kwargs_config[prefix_config_prefix] = config_prefix

        if (
            prefix_action_config in flat_group_kwargs_config
            and flat_group_kwargs_config[prefix_action_config]
        ):
            unflat_group_group_kwargs_config = flatten_dict.unflatten(
                flat_group_kwargs_config
            )
            kwargs_configurations.append(unflat_group_group_kwargs_config)
    return kwargs_configurations


def load_missing_action_kwargs(kwargs_configurations):
    flat_action_kwargs = {}
    for kwargs in kwargs_configurations:
        for group, args in kwargs.items():
            # Set group prefixes
            kwargs_path = (group,)
            if kwargs_path not in flat_action_kwargs:
                flat_action_kwargs[kwargs_path] = {}

            input_dict = find_value_in_dict(args, key="action_kwargs")
            required_fields = find_value_in_dict(args, key="valid_action_config")
            missing_dict = missing_fields(input_dict, required_fields)
            action_kwargs_flat_path = get_dict_path(
                args, key="action_kwargs", truncate=True
            )

            if action_kwargs_flat_path:
                dict_flat_path = action_kwargs_flat_path[:-1]
                if kwargs_path != dict_flat_path:
                    kwargs_path = kwargs_path + dict_flat_path
                    if kwargs_path not in flat_action_kwargs:
                        flat_action_kwargs[kwargs_path] = {}

            # Fill in the provided arguments
            flat_action_kwargs[kwargs_path] = input_dict

            config_prefix = find_value_in_dict(args, key="config_prefix")
            # Update with missing arguments from config
            loaded_from_config = load_from_config(missing_dict, prefix=config_prefix)
            flat_action_kwargs[kwargs_path].update(loaded_from_config)

    return flatten_dict.unflatten(flat_action_kwargs)


def get_dict_path(dictionary, key=None, multiple=False, truncate=False):
    if not key:
        return None
    flat_dict = flatten_dict.flatten(dictionary, keep_empty_types=(dict,))
    matches = []
    for k, v in flat_dict.items():
        if isinstance(k, (list, set, tuple)):
            for idx, k_v in enumerate(k):
                if k_v == key:
                    if truncate:
                        matches.append(k[: idx + 1])
                    else:
                        matches.append(k)
    if not matches:
        return None
    if multiple:
        return matches
    else:
        return matches[0]


def find_value_in_dict(dictionary, key=None, remain_dict=None):
    if not key:
        return None

    if not remain_dict:
        local_dict = copy.deepcopy(dictionary)
    else:
        local_dict = remain_dict

    if key in local_dict:
        return local_dict[key]

    keys = list(iter(local_dict))
    rand_key = keys[0]
    value = local_dict.pop(rand_key)

    if isinstance(value, dict):
        return find_value_in_dict(value, key=key, remain_dict=local_dict)
    return find_value_in_dict(local_dict, key=key, remain_dict=local_dict)


def create_sub_dictionaries(dictionary, tuple_keys):
    flat_dict = flatten_dict.flatten(dictionary)
    flat_dict[tuple_keys] = {}
    return flatten_dict.unflatten(flat_dict)


def remove_arguments(args, attributes, prefix=None):
    local_args = copy.deepcopy(args)
    if not attributes:
        return args

    for attribute in attributes:
        if prefix:
            attribute_path = "{}{}".format(prefix, attribute)
        else:
            attribute_path = "{}".format(attribute)
        if hasattr(local_args, attribute_path):
            delattr(local_args, attribute_path)

    return local_args
