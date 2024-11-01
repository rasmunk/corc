import jinja2
from corc.utils.io import load_yaml, exists


async def get_stack_config(deploy_file):
    # Load the architecture file and deploy the stack
    if not exists(deploy_file):
        return False
    stack_config = load_yaml(deploy_file)
    if not stack_config:
        return False
    return stack_config


async def extract_instance_config(instance_name, instance_kwargs):
    provider = instance_kwargs.get("provider", None)
    if not provider:
        return False, {
            "error": "Provider for node: {} is required.".format(instance_name)
        }

    instance_settings = instance_kwargs.get("settings", None)
    if not instance_settings:
        return False, {
            "error": "Settings for node: {} are required.".format(instance_name)
        }

    return True, {
        "provider": provider,
        "settings": instance_settings,
    }


async def recursively_prepare_instance_config(template_vars, instance_config):
    output_dict = {}
    # TODO, augment to support recursive templating
    if isinstance(instance_config, list):
        templated_list = []
        for config in instance_config:
            templated_list.append(
                await recursively_prepare_instance_config(template_vars, config)
            )
        return templated_list
    elif isinstance(instance_config, dict):
        for key, value in instance_config.items():
            output_dict[key] = await recursively_prepare_instance_config(
                template_vars, value
            )
    elif isinstance(instance_config, str):
        environment = jinja2.Environment()
        template = environment.from_string(instance_config)
        return template.render(template_vars)
    elif isinstance(instance_config, (int, float, bytes)):
        return instance_config
    return output_dict


async def get_stack_config_instances(stack_config):
    deploy_instance_configs = {}
    for instance_name, instance_kwargs in stack_config.get("instances", {}).items():
        if "[" in instance_name and "]" in instance_name:
            # Node range defined, unroll list
            start_string_index = instance_name.index("[")
            stop_string_index = instance_name.index("]")

            range_numbers = [
                int(number)
                for number in instance_name[
                    start_string_index + 1 : stop_string_index
                ].split("-")
            ]
            unrolled_instances = [
                "instance{:02d}".format(i)
                for i in range(range_numbers[0], range_numbers[1] + 1)
            ]

            for unrolled_instance in unrolled_instances:
                success, response = await extract_instance_config(
                    unrolled_instance, instance_kwargs
                )
                if not success:
                    return False, response
                instance_config = response
                instance_template_values = {
                    "instance": {
                        "name": unrolled_instance,
                    }
                }
                templated_instance_config = await recursively_prepare_instance_config(
                    instance_template_values, instance_config
                )
                deploy_instance_configs[unrolled_instance] = templated_instance_config
        else:
            success, response = await extract_instance_config(
                instance_name, instance_kwargs
            )
            if not success:
                return False, response
            instance_config = response
            instance_template_values = {
                "instance": {
                    "name": instance_name,
                }
            }
            templated_instance_config = await recursively_prepare_instance_config(
                instance_template_values, instance_config
            )
            deploy_instance_configs[instance_name] = templated_instance_config
    return True, deploy_instance_configs


async def get_stack_config_pools(stack_config):
    return stack_config.get("pools", {})
