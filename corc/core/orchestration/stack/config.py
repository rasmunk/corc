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


async def extract_node_config(node_name, node_kwargs):
    provider = node_kwargs.get("provider", None)
    if not provider:
        return False, {"error": "Provider for node: {} is required.".format(node_name)}

    node_settings = node_kwargs.get("settings", None)
    if not node_settings:
        return False, {"error": "Settings for node: {} are required.".format(node_name)}

    return True, {
        "provider": provider,
        "settings": node_settings,
    }


async def recursively_prepare_node_config(template_vars, node_config):
    output_dict = {}
    # TODO, augment to support recursive templating
    if isinstance(node_config, list):
        templated_list = []
        for config in node_config:
            templated_list.append(
                await recursively_prepare_node_config(template_vars, config)
            )
        return templated_list
    elif isinstance(node_config, dict):
        for key, value in node_config.items():
            output_dict[key] = await recursively_prepare_node_config(
                template_vars, value
            )
    elif isinstance(node_config, str):
        environment = jinja2.Environment()
        template = environment.from_string(node_config)
        return template.render(template_vars)
    elif isinstance(node_config, (int, float, bytes)):
        return node_config
    return output_dict


async def get_stack_config_nodes(stack_config):
    deploy_node_configs = {}
    for node_name, node_kwargs in stack_config.get("nodes", {}).items():
        if "[" in node_name and "]" in node_name:
            # Node range defined, unroll list
            start_string_index = node_name.index("[")
            stop_string_index = node_name.index("]")

            range_numbers = [
                int(number)
                for number in node_name[
                    start_string_index + 1 : stop_string_index
                ].split("-")
            ]
            unrolled_nodes = [
                "node{:02d}".format(i)
                for i in range(range_numbers[0], range_numbers[1] + 1)
            ]

            for unrolled_node in unrolled_nodes:
                success, response = await extract_node_config(
                    unrolled_node, node_kwargs
                )
                if not success:
                    return False, response
                node_config = response
                node_template_values = {
                    "node": {
                        "name": unrolled_node,
                    }
                }
                templated_node_config = await recursively_prepare_node_config(
                    node_template_values, node_config
                )
                deploy_node_configs[unrolled_node] = templated_node_config
        else:
            success, response = await extract_node_config(node_name, node_kwargs)
            if not success:
                return False, response
            deploy_node_configs[node_name] = response
    return True, deploy_node_configs
