# Description: Deploy the stack
import asyncio
from corc.core.defaults import STACK
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.helpers import import_from_module
from corc.core.orchestration.pool.models import Pool
from corc.core.plugins.plugin import discover, import_plugin
from corc.core.orchestration.stack.config import (
    get_stack_config,
    get_stack_config_instances,
)


async def provision_instance(instance_name, instance_details):
    plugin_driver = discover(instance_details["provider"]["name"])
    if not plugin_driver:
        return False, {
            "name": instance_name,
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
            "name": instance_name,
            "error": "Failed to load plugin: {}.".format(
                instance_details["provider"]["name"]
            ),
        }

    driver_client_func = import_from_module(
        "{}.{}".format(plugin_driver.name, "client"), "client", "new_client"
    )
    driver = driver_client_func(
        instance_details["provider"]["driver"], *driver_args, **driver_kwargs
    )
    if not driver:
        return False, {
            "name": instance_name,
            "error": "Failed to create client for provider driver: {}.".format(
                instance_details["provider"]["driver"]
            ),
        }

    provider_create_func = import_from_module(
        "{}.{}".format(plugin_driver.module, "create"), "create", "create"
    )
    return await provider_create_func(
        driver,
        *instance_details["settings"]["args"],
        **instance_details["settings"]["kwargs"]
    )


async def deploy(*args, **kwargs):
    name, deploy_file = args[0], args[1]
    stack_db = DictDatabase(STACK)

    if not await stack_db.exists():
        created = await stack_db.touch()
        if not created:
            return False, {"error": "Failed to create stack: {}.".format(name)}
    stack = {name: {}}

    # Load the architecture file and deploy the stack
    stack_config = await get_stack_config(deploy_file)
    if not stack_config:
        return False, {"error": "Failed to load stack config."}
    stack[name]["config"] = stack_config

    success, response = await get_stack_config_instances(stack_config)
    if not success:
        return False, response
    deploy_instances = response
    stack[name]["instances"] = []

    provision_tasks = [
        provision_instance(instance_name, instance_details)
        for instance_name, instance_details in deploy_instances.items()
    ]
    provision_results = await asyncio.gather(*provision_tasks)

    provisioned_instances, failed_instances = [], []
    for result in provision_results:
        if not result[0]:
            print("Failed to provision instance: {}.".format(result[1]["error"]))
            failed_instances.append(result[1]["error"])
        else:
            print("Provisioned instance: {}.".format(result[1]))
            provisioned_instances.append(result[1]["instance"])
            stack[name]["instances"].append(result[1]["instance"])

    provisioned_instance_names = {
        instance.name: instance for instance in provisioned_instances
    }
    stack[name]["pools"] = {}
    for pool_name, pool_kwargs in stack_config.get("pools", {}).items():
        pool = Pool(pool_name)
        stack[name]["pools"][pool_name] = pool
        for instance_name in pool_kwargs.get("instances", []):
            if instance_name not in provisioned_instance_names:
                return False, {
                    "error": "Instance: {} did not provision succesfully in the stack.".format(
                        instance_name
                    )
                }

            added = await pool.add(provisioned_instance_names[instance_name])
            if not added:
                return False, {
                    "error": "Failed to add instance: {} to pool: {}.".format(
                        instance_name, pool_name
                    )
                }
            else:
                print(
                    "Added instance: {} to pool: {}.".format(instance_name, pool_name)
                )
    saved = stack_db.add(stack)
    if not saved:
        return False, {"error": "Failed to save stack: {}.".format(name)}

    return True, {"msg": "Stack deployed successfully."}
