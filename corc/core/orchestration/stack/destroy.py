import asyncio
from corc.core.defaults import STACK
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.helpers import import_from_module
from corc.core.orchestration.pool.models import Pool
from corc.core.plugins.plugin import discover, import_plugin
from corc.core.orchestration.stack.config import (
    get_stack_config,
    get_stack_config_instances,
)


async def destroy_instance(instance_name, instance_details):
    plugin_driver = discover(instance_details["provider"]["name"])
    if not plugin_driver:
        return False, {
            "name": instance_name,
            "error": "Provider: {} is not installed.".format(
                instance_details["provider"]["name"]
            ),
        }
    plugin_module = import_plugin(plugin_driver.name, return_module=True)
    if not plugin_module:
        return False, {
            "name": instance_name,
            "error": "Failed to load plugin: {}.".format(
                instance_details["provider"]["name"]
            ),
        }

    driver_client_func = import_from_module(
        "{}.{}".format(plugin_driver.name, "client"), "client", "new_client"
    )
    driver = driver_client_func(instance_details["provider"]["driver"])
    if not driver:
        return False, {
            "name": instance_name,
            "error": "Failed to create client for provider driver: {}.".format(
                instance_details["provider"]["driver"]
            ),
        }

    provider_remove_func = import_from_module(
        "{}.{}".format(plugin_driver.module, "remove"), "remove", "remove"
    )
    return await provider_remove_func(driver, instance_name)


async def destroy(*args, **kwargs):
    name, deploy_file = args[0], args[1]
    stack_db = DictDatabase(STACK)
    if not await stack_db.exists(name):
        return False, {"error": "Stack: {} does not exist.".format(name)}

    # Load the architecture file and deploy the stack
    stack_config = await get_stack_config(deploy_file)
    if not stack_config:
        return False, {"error": "Failed to load stack config."}

    success, response = await get_stack_config_instances(stack_config)
    if not success:
        return False, response
    remove_instances = response

    remove_tasks = [
        destroy_instance(instance_name, instance_details)
        for instance_name, instance_details in remove_instances.items()
    ]
    remove_results = await asyncio.gather(*remove_tasks)

    removed_instances, not_removed_instances = [], []
    for result in remove_results:
        if result[0]:
            removed_instances.append(result[1])
            await stack_db.remove(result[1])
        else:
            not_removed_instances.append(result[1])

    removed_instance_names = {instance.name: instance for instance in removed_instances}
    for pool_name, pool_kwargs in stack_config.get("pools", {}).items():
        pool = Pool(pool_name)
        for instance_name in pool_kwargs.get("instances", []):
            if instance_name not in removed_instances:
                return False, {
                    "error": "Instance: {} did not provision succesfully in the stack.".format(
                        instance_name
                    )
                }

            removed = await pool.remove(removed_instances[instance_name])
            if not removed:
                return False, {
                    "error": "Failed to remove Instance: {} to pool: {}.".format(
                        instance_name, pool_name
                    )
                }
        removed = await stack_db.remove(pool_name)
        if not removed:
            return False, {
                "error": "Failed to remove pool: {} from stack.".format(pool_name)
            }

    return True, {"msg": "Stack: {} has been destroyed.".format(name)}
