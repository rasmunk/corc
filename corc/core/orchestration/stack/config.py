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


async def recursive_template_node_config(template_vars, node_details, node_config):
    # TODO, augment to support recursive templating
    if isinstance(node_config, list):
        for config in node_config:
            return await recursive_template_node_config(template, node_details, config)
    elif isinstance(node_config, dict):
        for key, value in node_config.items():
            node_config[key] = await recursive_template_node_config(
                template, node_details, value
            )
    elif isinstance(node_config, str):
        template.generate()
        template = jinja_environment.from_string(node_config)

    return template.render(node_details)


async def template_node_config(node_details, node_config):
    new_node_config = {}
    environment = jinja2.Environment()
    for key, value in node_config.items():
        template = environment.from_string(value)
        new_node_config[key] = template.render(node_details)
    return new_node_config


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
                node_details = {
                    "node": {
                        "name": unrolled_node,
                    }
                }
                templated_node_config = await template_node_config(
                    node_details, node_config
                )
                deploy_node_configs[unrolled_node] = templated_node_config
        else:
            success, response = await extract_node_config(node_name, node_kwargs)
            if not success:
                return False, response
            deploy_node_configs[node_name] = response

    return True, deploy_node_configs
