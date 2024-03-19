# Description: Deploy the stack
import asyncio
from corc.utils.io import load_yaml, exists
from corc.core.orchestration.pool.models import Pool, Node
from corc.core.plugins.plugin import discover, import_plugin


async def get_stack_config(deploy_file):
    # Load the architecture file and deploy the stack
    if not exists(deploy_file):
        return False
    stack_config = load_yaml(deploy_file)
    if not stack_config:
        return False
    return stack_config


async def get_deploy_node_configs(stack_config):
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


async def provision_node(node_name, node_details):
    plugin_driver = discover(node_details["provider"])
    if not plugin_driver:
        return False, {
            "name": node_name,
            "error": "Provider: {} is not installed.".format(node_details["provider"]),
        }
    plugin_module = import_plugin(plugin_driver.name, return_module=True)
    if not plugin_module:
        return False, {
            "name": node_name,
            "error": "Failed to load plugin: {}.".format(node_details["provider"]),
        }

    driver_client = plugin_driver.client.new_client(plugin_driver)
    if not driver_client:
        return False, {
            "name": node_name,
            "error": "Failed to create provider client for: {}.".format(
                node_details["provider"]
            ),
        }

    return await create(driver_client, node_details["node"])


async def deploy(*args, **kwargs):
    name, deploy_file = args[0], args[1]

    # Load the architecture file and deploy the stack
    stack_config = await get_stack_config(deploy_file)
    if not stack_config:
        return False, {"error": "Failed to load stack config."}

    success, response = await get_deploy_node_configs(stack_config)
    if not success:
        return False, response
    deploy_nodes = response

    provision_tasks = [
        provision_node(node_name, node_details)
        for node_name, node_details in deploy_nodes.items()
    ]
    provision_results = await asyncio.gather(*provision_tasks)

    provisioned_nodes, failed_nodes = [], []
    for result in provision_results:
        if not result[0]:
            print("Failed to provision node: {}.".format(result[1]["error"]))
            failed_nodes.append(result[1]["error"])
        else:
            print("Provisioned node: {}.".format(result[1]["node"]))
            provisioned_nodes.append(result[1])

    for pool_name, pool_kwargs in stack_config.get("pools", {}).items():
        pool = Pool(pool_name)
        for node_name in pool_kwargs.get("nodes", []):
            if node_name not in provisioned_nodes:
                return False, {
                    "error": "Node: {} did not provision succesfully in the stack.".format(
                        node_name
                    )
                }

            added = await pool.add(provisioned_nodes[node_name]["node"])
            if not added:
                return False, {
                    "error": "Failed to add node: {} to pool: {}.".format(
                        node_name, pool_name
                    )
                }
    return True, {"msg": "Stack deployed successfully."}
