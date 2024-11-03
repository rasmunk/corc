import asyncio
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.helpers import import_from_module
from corc.core.orchestration.pool.models import Pool
from corc.core.plugins.plugin import discover, import_plugin


async def destroy_instance(instance_id, instance_details):
    response = {}
    plugin_driver = discover(instance_details["provider"]["name"])
    if not plugin_driver:
        response["id"] = instance_id
        response["msg"] = "Provider: {} is not installed.".format(
            instance_details["provider"]["name"]
        )
        return False, response

    driver_args = []
    if "args" in instance_details["provider"]:
        driver_args = instance_details["provider"]["args"]

    driver_kwargs = {}
    if "kwargs" in instance_details["provider"]:
        driver_kwargs = instance_details["provider"]["kwargs"]

    plugin_module = import_plugin(plugin_driver.name, return_module=True)
    if not plugin_module:
        response["id"] = instance_id
        response["msg"] = "Failed to load plugin: {}.".format(
            instance_details["provider"]["name"]
        )
        return False, response

    driver_client_func = import_from_module(
        "{}.{}".format(plugin_driver.name, "client"), "client", "new_client"
    )
    driver = driver_client_func(
        instance_details["provider"]["driver"],
        *driver_args,
        **driver_kwargs,
    )
    if not driver:
        response["id"] = instance_id
        response["msg"] = "Failed to create client for provider driver: {}.".format(
            instance_details["provider"]["driver"]
        )
        return False, response

    provider_remove_func = import_from_module(
        "{}.{}".format(plugin_driver.module, "remove"), "remove", "remove"
    )
    return await provider_remove_func(driver, instance_id)


async def get_instance(instance_id, instance_details):
    response = {}
    plugin_driver = discover(instance_details["provider"]["name"])
    if not plugin_driver:
        response["id"] = instance_id
        response["msg"] = "Provider: {} is not installed.".format(
            instance_details["provider"]["name"]
        )
        return False, response

    driver_args = []
    if "args" in instance_details["provider"]:
        driver_args = instance_details["provider"]["args"]

    driver_kwargs = {}
    if "kwargs" in instance_details["provider"]:
        driver_kwargs = instance_details["provider"]["kwargs"]

    plugin_module = import_plugin(plugin_driver.name, return_module=True)
    if not plugin_module:
        response["id"] = instance_id
        response["msg"] = "Failed to load plugin: {}.".format(
            instance_details["provider"]["name"]
        )
        return False, response

    driver_client_func = import_from_module(
        "{}.{}".format(plugin_driver.name, "client"), "client", "new_client"
    )
    driver = driver_client_func(
        instance_details["provider"]["driver"],
        *driver_args,
        **driver_kwargs,
    )
    if not driver:
        resonse["id"] = instance_id
        response["msg"] = "Failed to create client for provider driver: {}.".format(
            instance_details["provider"]["driver"]
        )
        return False, response

    provider_get_func = import_from_module(
        "{}.{}".format(plugin_driver.module, "get"), "get", "get"
    )
    return await provider_get_func(driver, instance_id)


async def destroy(*args, **kwargs):
    response = {}
    name = args[0]
    directory = kwargs.get("directory", None)

    stack_db = DictDatabase(name, directory=directory)
    if not await stack_db.exists():
        response["msg"] = (
            "The Stack {} does not exist, so it can't be destroyed.".format(name)
        )
        return False, response

    stack = await stack_db.get(name)
    if not stack:
        response["msg"] = "Stack: {} does not exist.".format(name)
        return False, response

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
    remove_results = await asyncio.gather(*remove_tasks)
    for result in remove_results:
        if not result[0]:
            print("Failed to remove Instance: {}.".format(result["id"]))

    # Update the stack config
    for instance_id, instance_details in remove_instance_details.items():
        found_instance = await get_instance(instance_id, instance_details["config"])
        if not found_instance[0]:
            stack["config"]["instances"].pop(instance_details["name"])
            stack["instances"].pop(instance_details["name"])

    # Persist the changes to the stack
    updated = await stack_db.update(name, stack)
    if not updated:
        response["msg"] = "Failed to update Stack: {} after removing Instances".format(
            name
        )
        return False, response

    # Remove the pools
    # TODO, extract to an async function that is gathered
    for pool_name, pool_kwargs in stack["config"]["pools"].items():
        pool = Pool(pool_name)
        for instance_name in pool_kwargs.get("instances", []):
            if instance_name not in stack["instances"]:
                for instance in await pool.find("name", instance_name):
                    if not await pool.remove(instance.id):
                        response["msg"] = (
                            "Failed to remove Instance: {} from Pool: {}.".format(
                                instance.id, pool.name
                            )
                        )
                        return False, response

        if await pool.is_empty():
            if await pool.remove_persistence():
                stack["pools"].pop(pool_name)

    if not await stack_db.remove(name):
        response["msg"] = "Failed to remove Stack: {}.".format(name)
        return False, response

    if await stack_db.is_empty() and not await stack_db.remove_persistence():
        response["msg"] = "Failed to remove Stack persistence: {}.".format(name)
        return False, response

    response["msg"] = "Stack: {} has been destroyed.".format(name)
    return True, response
