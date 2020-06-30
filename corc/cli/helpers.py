from argparse import Namespace
import flatten_dict
from corc.cli.args import extract_arguments
from corc.cli.providers.helpers import select_provider
from corc.config import (
    load_config,
    load_from_config,
    corc_config_groups,
    gen_config_prefix,
    gen_config_provider_prefix,
)
from corc.providers.oci.config import oci_config_groups
from corc.defaults import PROVIDERS_LOWER
from corc.util import missing_fields


def cli_exec(args):
    # action determines which function to execute
    module_path = args.module_path
    module_name = args.module_name
    func_name = args.func_name
    argument_groups = args.argument_groups
    if hasattr(args, "provider_groups"):
        provider_groups = args.provider_groups
    else:
        provider_groups = []

    provider, provider_kwargs = prepare_provider_kwargs(args, namespace_wrap=True)
    if provider:
        module_path = module_path.format(provider=provider)
        # load missing provider kwargs from config
        provider_configuration = prepare_kwargs_configurations(
            provider_kwargs, provider_groups, strip_group_prefix=False
        )
        provider_kwargs = load_missing_action_kwargs(provider_configuration)

    func = import_from_module(module_path, module_name, func_name)
    if not func:
        return False

    # Extract kwargs from args
    kwargs_configuration = prepare_kwargs_configurations(args, argument_groups)
    # Load config and fill in missing values
    action_kwargs = load_missing_action_kwargs(kwargs_configuration)

    if provider:
        return func(provider_kwargs, **action_kwargs)
    return func(**action_kwargs)


def import_from_module(module_path, module_name, func_name):
    module = __import__(module_path, fromlist=[module_name])
    return getattr(module, func_name)


def prepare_provider_kwargs(args, namespace_wrap=False):
    providers = vars(extract_arguments(args, PROVIDERS_LOWER, strip_group_prefix=False))
    provider = select_provider(providers, default_fallback=True, verbose=True)
    provider_kwargs = vars(extract_arguments(args, [provider]))
    # remove the provider flag
    provider_kwargs.pop(provider)
    if namespace_wrap:
        provider_kwargs = Namespace(**provider_kwargs)
    return provider, provider_kwargs


def prepare_kwargs_configurations(args, argument_groups, strip_group_prefix=True):
    # Try to find all available args
    kwargs_configurations = []
    for group in argument_groups:
        group_kwargs_config = {}
        name = group.lower()
        if "_" in name:
            prefix = tuple(name.split("_"))
            group_kwargs_config = create_sub_dictionaries(group_kwargs_config, prefix)
        else:
            prefix = (name,)
            group_kwargs_config[name] = {}

        # TODO, subname on split prefix
        action_kwargs = vars(extract_arguments(args, [group]))
        if action_kwargs:
            group_kwargs_config[name]["action_kwargs"] = action_kwargs
        else:
            group_kwargs_config[name]["action_kwargs"] = {}

        if group in corc_config_groups:
            valid_action_config = corc_config_groups[group]
            # gen config prefix
            config_prefix = gen_config_prefix(prefix)
            group_kwargs_config[name]["valid_action_config"] = valid_action_config
            group_kwargs_config[name]["config_prefix"] = config_prefix

        if group in oci_config_groups:
            valid_action_config = oci_config_groups[group]
            prefix = ("oci",) + prefix
            config_prefix = gen_config_provider_prefix(prefix)
            group_kwargs_config[name]["valid_action_config"] = valid_action_config
            group_kwargs_config[name]["config_prefix"] = config_prefix

        if (
            group_kwargs_config[name]
            and "valid_action_config" in group_kwargs_config[name]
        ):
            kwargs_configurations.append(group_kwargs_config)
    return kwargs_configurations


def load_missing_action_kwargs(kwargs_configurations):
    action_kwargs = {}
    config = load_config()
    for kwargs in kwargs_configurations:
        for group, args in kwargs.items():
            action_kwargs[group] = {}
            missing_dict = missing_fields(
                args["action_kwargs"], args["valid_action_config"]
            )
            action_kwargs[group].update(
                load_from_config(
                    missing_dict, prefix=args["config_prefix"], config=config
                )
            )
    return action_kwargs


def create_sub_dictionaries(dictionary, tuple_keys):
    flat_dict = flatten_dict.flatten(dictionary)
    flat_dict[tuple_keys] = {}
    return flatten_dict.unflatten(flat_dict)
