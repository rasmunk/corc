from argparse import Namespace
import copy
import flatten_dict
from corc.cli.args import extract_arguments, wrap_extract_arguments

# from corc.cli.input_groups.providers.helpers import select_provider
from corc.core.config import (
    load_from_config,
    corc_config_groups,
    gen_config_prefix,
    gen_config_provider_prefix,
)
from corc.core.helpers import import_from_module
from corc.core.util import missing_fields
from corc.core.providers.config import get_provider_config_groups


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

    if hasattr(args, "skip_groups"):
        skip_groups = args.skip_groups
    else:
        skip_groups = []

    func = import_from_module(module_path, module_name, func_name)
    if not func:
        return False

    action_kwargs = get_action_kwargs(args, argument_groups)

    provider_kwargs = get_provider_kwargs(args, provider_groups)

    extra_action_kwargs = get_extra_action_kwargs(
        args, skip_groups=[argument_groups, provider_groups]
    )
    # get_action_kwargs()

    # get_provider_kwargs()

    # get_extra_action_kwargs()

    # provider, provider_kwargs = prepare_provider_kwargs(args, namespace_wrap=True)
    # if provider:
    #     # Load the specific provider config module
    #     module_path = module_path.format(provider=provider)
    #     # Find the missing cli provider kwargs
    #     provider_kwargs_configuration = prepare_kwargs_configurations(
    #         provider_kwargs,
    #         provider_groups,
    #         provider=provider,
    #         strip_group_prefix=False)
    # # Load the missing cli provider kwargs from the config
    # provider_kwargs = load_missing_action_kwargs(provider_kwargs_configuration)

    # Prepare both the arguments provided for the given group
    # and mark the arguments that are missing and that should be
    # loaded from the config file
    # kwargs_configuration = prepare_kwargs_configurations(args, argument_groups)
    # Load config and fill in missing values
    # action_kwargs = load_missing_action_kwargs(kwargs_configuration)

    # Combine the provided kwargs with the missing loaded kwargs

    # Extract the remaining skipped config groups into the extra_action_kwargs
    # extra_action_kwargs = prepare_none_config_kwargs(args, skip_config_groups)
    # if provider:
    #     return func(provider, provider_kwargs, **action_kwargs, **extra_action_kwargs)
    return func(**action_kwargs, **extra_action_kwargs)


def get_action_kwargs(arguments, groups=None):
    if not groups:
        groups = []


def prepare_none_config_kwargs(args, skip_config_groups_groups):
    kwargs = wrap_extract_arguments(args, skip_config_groups_groups)
    return kwargs


def prepare_provider_kwargs(args, providers=None, namespace_wrap=False):
    """ Prepare and extract the arguments that are associated with the selected
    provider """
    if not providers:
        providers = []

    # Extract the arguments in the args that are associated with a provider
    # as indicated by their --providername-arg flags.
    providers = vars(extract_arguments(args, providers, strip_group_prefix=False))
    # Select the provider used (For now this is singular)
    provider = select_provider(providers, default_fallback=True, verbose=True)

    provider_kwargs = {}
    if provider:
        # Extract only the selected provider
        provider_kwargs = vars(extract_arguments(args, [provider]))
        # remove the provider flag
        provider_kwargs.pop(provider)
    if namespace_wrap:
        provider_kwargs = Namespace(**provider_kwargs)
    return provider, provider_kwargs


def prepare_kwargs_configurations(
    args, argument_groups, provider=False, strip_group_prefix=True
):
    """ Discover which arguments are required for the given argument group and
        designate which needs to be loaded from the underlying configuration
        file and which have already been provided on the CLI.
        This prepares the kwargs_configuration dictionary that is subsequently 
        used by load_missing_action_kwargs to load the values that are required
        by the given action from a configuration file. 
    """
    # Try to find all available args for the given argument_group
    kwargs_configurations = []
    for group in argument_groups:
        group_kwargs_config = {}
        group_name = group.lower()
        # Flat group_kwargs_config to do direct indexing
        if "_" in group_name:
            group_prefix = tuple(group_name.split("_"))
            group_kwargs_config = create_sub_dictionaries(
                group_kwargs_config, group_prefix
            )
        else:
            group_prefix = (group_name,)
            group_kwargs_config[group_name] = {}

        # arguments provided on the CLI
        prefix_action_kwargs = group_prefix + ("action_kwargs",)
        prefix_action_config = group_prefix + ("valid_action_config",)
        prefix_config_prefix = group_prefix + ("config_prefix",)

        flat_group_kwargs_config = flatten_dict.flatten(
            group_kwargs_config, keep_empty_types=(dict,)
        )
        # TODO, subname on split group_prefix
        action_kwargs = vars(extract_arguments(args, [group]))
        if action_kwargs:
            # Remove already claimed action_kwargs from args
            # since we don't need to load them from the configuration since they are
            # already present
            args = remove_arguments(args, action_kwargs.keys(), prefix=group_name + "_")
            flat_group_kwargs_config[prefix_action_kwargs] = action_kwargs
        else:
            flat_group_kwargs_config[prefix_action_kwargs] = {}

        if group in corc_config_groups:
            valid_action_config = corc_config_groups[group]
            # Extract the PACKAGE_NAME prefix at which the group_name should evntually be
            # extracted from a configuration file
            config_prefix = gen_config_prefix(group_prefix)
            flat_group_kwargs_config[prefix_action_config] = valid_action_config
            flat_group_kwargs_config[prefix_config_prefix] = config_prefix

        if provider:
            provider_groups = get_provider_config_groups(provider)
            if group in provider_groups:
                valid_action_config = provider_groups[group]
                provider_prefix = (provider,) + group_prefix
                config_prefix = gen_config_provider_prefix(provider_prefix)
                flat_group_kwargs_config[prefix_action_config] = valid_action_config
                flat_group_kwargs_config[prefix_config_prefix] = config_prefix

        if (
            prefix_action_config in flat_group_kwargs_config
            and flat_group_kwargs_config[prefix_action_config]
        ):
            unflatten_group_kwargs_config = flatten_dict.unflatten(
                flat_group_kwargs_config
            )
            kwargs_configurations.append(unflatten_group_kwargs_config)
    return kwargs_configurations


def load_missing_action_kwargs(kwargs_configurations):
    flat_action_kwargs = {}
    for kwargs in kwargs_configurations:
        for group, args in kwargs.items():
            # Set group prefixes
            kwargs_path = (group,)
            if kwargs_path not in flat_action_kwargs:
                flat_action_kwargs[kwargs_path] = {}

            # Extract the arguments provided by the CLI
            input_dict = find_value_in_dict(args, key="action_kwargs")
            # Find the required arguments that are valid_action_config values
            required_fields = find_value_in_dict(args, key="valid_action_config")
            # Determine and define which arguments are missing
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
            # Update the missing arguments with the values from the config
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
