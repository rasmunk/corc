from corc.utils.io import load_yaml, exists


async def get_stack_config(deploy_file):
    # Load the architecture file and deploy the stack
    if not exists(deploy_file):
        return False
    stack_config = load_yaml(deploy_file)
    if not stack_config:
        return False
    return stack_config


async def get_stack_config_nodes(stack_config):
    deploy_node_configs = {}
    for node_name, node_kwargs in stack_config.get("nodes", {}).items():
        provider = node_kwargs.get("provider", None)
        if not provider:
            return False, {
                "error": "Provider for node: {} is required.".format(node_name)
            }

        node_settings = node_kwargs.get("settings", None)
        if not node_settings:
            return False, {
                "error": "Settings for node: {} are required.".format(node_name)
            }

        deploy_node_configs[node_name] = {
            "provider": provider,
            "settings": node_settings,
        }
    return True, deploy_node_configs
