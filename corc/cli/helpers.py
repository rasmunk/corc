from corc.cli.args import extract_arguments
from corc.cli.providers.helpers import select_provider
from corc.config import (
    load_config,
    load_from_config,
    corc_config_groups,
    gen_config_prefix,
    gen_config_provider_prefix,
)
from corc.providers.oci import oci_config_groups
from corc.defaults import PROVIDER, ACTION_GROUPS
from corc.util import missing_fields


def cli_exec(args):
    # action determines which function to execute
    module_path = args.module_path
    module_name = args.module_name
    func_name = args.func_name

    provider, provider_kwargs = prepare_provider_kwargs(args)

    if provider:
        module_path.format(provider=provider)

    func = import_from_module(module_path, module_name, func_name)
    if not func:
        return False

    # Extract kwargs from args
    action_kwargs = prepare_kwargs_configurations(args)
    # Load config and fill in missing values
    action_kwargs = load_missing_action_kwargs(action_kwargs)

    if provider:
        return func(provider, provider_kwargs, **action_kwargs)
    return func(**action_kwargs)


def import_from_module(module_path, module_name, func_name):
    module = __import__(module_path, fromlist=[module_name])
    return getattr(module, func_name)


def prepare_provider_kwargs(args):
    provider_kwargs = vars(extract_arguments(args, [PROVIDER]))
    provider = select_provider(provider_kwargs, default_fallback=True, verbose=True)
    return provider, provider_kwargs


def prepare_kwargs_configurations(args):
    # Try to find all available args
    kwargs_configurations = []
    for group in ACTION_GROUPS:
        group_kwargs_config = {}
        action_kwargs = vars(extract_arguments(args, [group]))
        if action_kwargs:
            group_kwargs_config.update(dict(action_kwargs=action_kwargs))

        if group in corc_config_groups:
            valid_action_config = corc_config_groups[group]
            # gen config prefix
            config_prefix = gen_config_prefix({group.lower(): {}})
            group_kwargs_config.update(
                dict(
                    valid_action_config=valid_action_config, config_prefix=config_prefix
                )
            )

        if group in oci_config_groups:
            valid_action_config = oci_config_groups[group]
            config_prefix = gen_config_provider_prefix({"oci": {group: {}}})
            group_kwargs_config.update(
                dict(
                    valid_action_config=valid_action_config, config_prefix=config_prefix
                )
            )

        kwargs_configurations.append(group_kwargs_config)
    return kwargs_configurations


def load_missing_action_kwargs(kwargs_configurations):
    action_kwargs = {}
    config = load_config()
    for kwargs in kwargs_configurations.items():
        missing_dict = missing_fields(
            kwargs["action_kwargs"], kwargs["valid_action_config"]
        )
        action_kwargs.update(
            load_from_config(
                missing_dict, prefix=kwargs["config_prefix"], config=config
            )
        )
    return action_kwargs
