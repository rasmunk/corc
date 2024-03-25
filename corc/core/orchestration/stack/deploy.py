# Description: Deploy the stack
import asyncio
from corc.core.helpers import import_from_module
from corc.core.orchestration.pool.models import Pool
from corc.core.plugins.plugin import discover, import_plugin
from corc.core.orchestration.stack.config import (
    get_stack_config,
    get_stack_config_nodes,
)


async def provision_node(node_name, node_details):
    plugin_driver = discover(node_details["provider"]["name"])
    if not plugin_driver:
        return False, {
            "name": node_name,
            "error": "Provider: {} is not installed.".format(
                node_details["provider"]["name"]
            ),
        }

    driver_args = []
    if "args" in node_details["provider"]:
        driver_args = node_details["provider"]["args"]

    driver_kwargs = {}
    if "kwargs" in node_details["provider"]:
        driver_kwargs = node_details["provider"]["kwargs"]

    plugin_module = import_plugin(plugin_driver.name, return_module=True)
    if not plugin_module:
        return False, {
            "name": node_name,
            "error": "Failed to load plugin: {}.".format(
                node_details["provider"]["name"]
            ),
        }

    driver_client_func = import_from_module(
        "{}.{}".format(plugin_driver.name, "client"), "client", "new_client"
    )
    driver = driver_client_func(
        node_details["provider"]["driver"], *driver_args, **driver_kwargs
    )
    if not driver:
        return False, {
            "name": node_name,
            "error": "Failed to create client for provider driver: {}.".format(
                node_details["provider"]["driver"]
            ),
        }

    provider_create_func = import_from_module(
        "{}.{}".format(plugin_driver.module, "create"), "create", "create"
    )
    return await provider_create_func(
        driver, *node_details["settings"]["args"], **node_details["settings"]["kwargs"]
    )


async def deploy(*args, **kwargs):
    name, deploy_file = args[0], args[1]

    # Load the architecture file and deploy the stack
    stack_config = await get_stack_config(deploy_file)
    if not stack_config:
        return False, {"error": "Failed to load stack config."}

    success, response = await get_stack_config_nodes(stack_config)
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
            print("Provisioned node: {}.".format(result[1]))
            provisioned_nodes.append(result[1]["instance"])

    provisioned_node_names = {node.name: node for node in provisioned_nodes}
    for pool_name, pool_kwargs in stack_config.get("pools", {}).items():
        pool = Pool(pool_name)
        for node_name in pool_kwargs.get("nodes", []):
            if node_name not in provisioned_node_names:
                return False, {
                    "error": "Node: {} did not provision succesfully in the stack.".format(
                        node_name
                    )
                }

            added = await pool.add(provisioned_node_names[node_name])
            if not added:
                return False, {
                    "error": "Failed to add node: {} to pool: {}.".format(
                        node_name, pool_name
                    )
                }
    return True, {"msg": "Stack deployed successfully."}
