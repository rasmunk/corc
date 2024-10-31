import asyncio
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.helpers import import_from_module
from corc.core.orchestration.pool.models import Pool
from corc.core.plugins.plugin import discover, import_plugin


async def destroy_instance(instance_id, instance_details):
    plugin_driver = discover(instance_details["provider"]["name"])
    if not plugin_driver:
        return False, {
            "id": instance_id,
            "error": "Provider: {} is not installed.".format(
                instance_details["provider"]["name"]
            ),
        }

    driver_args = []
    if "args" in instance_details["provider"]:
        driver_args = instance_details["provider"]["args"]

    driver_kwargs = {}
    if "kwargs" in instance_details["provider"]:
        driver_kwargs = instance_details["provider"]["kwargs"]

    plugin_module = import_plugin(plugin_driver.name, return_module=True)
    if not plugin_module:
        return False, {
            "id": instance_id,
            "error": "Failed to load plugin: {}.".format(
                instance_details["provider"]["name"]
            ),
        }

    driver_client_func = import_from_module(
        "{}.{}".format(plugin_driver.name, "client"), "client", "new_client"
    )
    driver = driver_client_func(
        instance_details["provider"]["driver"],
        *driver_args,
        **driver_kwargs,
    )
    if not driver:
        return False, {
            "id": instance_id,
            "error": "Failed to create client for provider driver: {}.".format(
                instance_details["provider"]["driver"]
            ),
        }

    provider_remove_func = import_from_module(
        "{}.{}".format(plugin_driver.module, "remove"), "remove", "remove"
    )
    return await provider_remove_func(driver, instance_id)


async def get_instance(instance_id, instance_details):
    plugin_driver = discover(instance_details["provider"]["name"])
    if not plugin_driver:
        return False, {
            "id": instance_id,
            "error": "Provider: {} is not installed.".format(
                instance_details["provider"]["name"]
            ),
        }

    driver_args = []
    if "args" in instance_details["provider"]:
        driver_args = instance_details["provider"]["args"]

    driver_kwargs = {}
    if "kwargs" in instance_details["provider"]:
        driver_kwargs = instance_details["provider"]["kwargs"]

    plugin_module = import_plugin(plugin_driver.name, return_module=True)
    if not plugin_module:
        return False, {
            "id": instance_id,
            "error": "Failed to load plugin: {}.".format(
                instance_details["provider"]["name"]
            ),
        }

    driver_client_func = import_from_module(
        "{}.{}".format(plugin_driver.name, "client"), "client", "new_client"
    )
    driver = driver_client_func(
        instance_details["provider"]["driver"],
        *driver_args,
        **driver_kwargs,
    )
    if not driver:
        return False, {
            "id": instance_id,
            "error": "Failed to create client for provider driver: {}.".format(
                instance_details["provider"]["driver"]
            ),
        }

    provider_get_func = import_from_module(
        "{}.{}".format(plugin_driver.module, "get"), "get", "get"
    )
    return await provider_get_func(driver, instance_id)


async def destroy(*args, **kwargs):
    name = args[0]
    directory = kwargs.get("directory", None)

    stack_db = DictDatabase(name, directory=directory)
    if not await stack_db.exists():
        return False, {
            "error": "The Stack {} does not exist, so it can't be destroyed.".format(
                name
            )
        }

    stack = await stack_db.get(name)
    if not stack:
        return False, {"error": "Stack: {} does not exist.".format(name)}

    remove_instance_details = {}
    for live_name in stack["instances"]:
        for config_name in stack["config"]["instances"]:
            if live_name == config_name:
                remove_instance_details[stack["instances"][live_name].id] = {
                    "name": live_name,
                    "config": stack["config"]["instances"][config_name],
                }
    # Remove the instances
    remove_tasks = [
        destroy_instance(instance_id, instance_details["config"])
        for instance_id, instance_details in remove_instance_details.items()
    ]
    _ = await asyncio.gather(*remove_tasks)

    # Update the stack config
    for instance_id, instance_details in remove_instance_details.items():
        found_instance = await get_instance(instance_id, instance_details["config"])
        if not found_instance[0]:
            stack["config"]["instances"].pop(instance_details["name"])
            stack["instances"].pop(instance_details["name"])

    # Persist the changes to the stack
    updated = await stack_db.update(name, stack)
    if not updated:
        return False, {
            "error": "Failed to update Stack: {} after removing Instances".format(name)
        }

    # Remove the pools
    for pool_name, pool_kwargs in stack["config"]["pools"].items():
        pool = Pool(pool_name)
        for instance_name in pool_kwargs.get("instances", []):
            if instance_name not in stack["instances"]:
                for instance in await pool.find("name", instance_name):
                    if not await pool.remove(instance.id):
                        return False, {
                            "error": "Failed to remove Instance: {} from Pool: {}.".format(
                                instance_name, pool_name
                            )
                        }
        if await pool.is_empty():
            if await pool.remove_persistence():
                stack["pools"].pop(pool_name)

    if not await stack_db.remove(name):
        return False, {"error": "Failed to remove stack: {}.".format(name)}

    if await stack_db.is_empty() and not await stack_db.remove_persistence():
        return False, {"error": "Failed to remove stack persistence: {}.".format(name)}

    return True, {"msg": "Stack: {} has been destroyed.".format(name)}
