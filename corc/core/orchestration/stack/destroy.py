import asyncio
from corc.core.defaults import STACK
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.helpers import import_from_module
from corc.core.orchestration.pool.models import Pool
from corc.core.plugins.plugin import discover, import_plugin
from corc.core.orchestration.stack.config import (
    get_stack_config,
    get_stack_config_nodes,
)


async def destroy_node(node_name, node_details):
    plugin_driver = discover(node_details["provider"]["name"])
    if not plugin_driver:
        return False, {
            "name": node_name,
            "error": "Provider: {} is not installed.".format(
                node_details["provider"]["name"]
            ),
        }
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
    driver = driver_client_func(node_details["provider"]["driver"])
    if not driver:
        return False, {
            "name": node_name,
            "error": "Failed to create client for provider driver: {}.".format(
                node_details["provider"]["driver"]
            ),
        }

    provider_remove_func = import_from_module(
        "{}.{}".format(plugin_driver.module, "remove"), "remove", "remove"
    )
    return await provider_remove_func(driver, node_name)


async def destroy(*args, **kwargs):
    name, deploy_file = args[0], args[1]
    stack_db = DictDatabase(STACK)
    if not await stack_db.exists(name):
        return False, {"error": "Stack: {} does not exist.".format(name)}

    # Load the architecture file and deploy the stack
    stack_config = await get_stack_config(deploy_file)
    if not stack_config:
        return False, {"error": "Failed to load stack config."}

    success, response = await get_stack_config_nodes(stack_config)
    if not success:
        return False, response
    remove_nodes = response

    remove_tasks = [
        destroy_node(node_name, node_details)
        for node_name, node_details in remove_nodes.items()
    ]
    remove_results = await asyncio.gather(*remove_tasks)

    removed_nodes, not_removed_nodes = [], []
    for result in remove_results:
        if result[0]:
            removed_nodes.append(result[1])
            await stack_db.remove(result[1])
        else:
            not_removed_nodes.append(result[1])

    removed_node_names = {node.name: node for node in removed_nodes}
    for pool_name, pool_kwargs in stack_config.get("pools", {}).items():
        pool = Pool(pool_name)
        for node_name in pool_kwargs.get("nodes", []):
            if node_name not in removed_nodes:
                return False, {
                    "error": "Node: {} did not provision succesfully in the stack.".format(
                        node_name
                    )
                }

            removed = await pool.remove(removed_nodes[node_name])
            if not removed:
                return False, {
                    "error": "Failed to remove node: {} to pool: {}.".format(
                        node_name, pool_name
                    )
                }
        removed = await stack_db.remove(pool_name)
        if not removed:
            return False, {
                "error": "Failed to remove pool: {} from stack.".format(pool_name)
            }

    return True, {"msg": "Stack: {} has been destroyed.".format(name)}
