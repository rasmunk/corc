# Description: Deploy the stack
import asyncio
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.helpers import import_from_module
from corc.core.plugins.plugin import discover, import_plugin


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
    name = args[0]
    directory = kwargs.get("directory", None)

    stack_db = DictDatabase(name, directory=directory)
    if not await stack_db.exists():
        return False, {
            "error": "The specified Stack to deploy: {} does not exists.".format(name)
        }

    stack_to_deploy = await stack_db.get(name)
    if not stack_to_deploy:
        return False, {
            "error": "Failed to find a Stack with name: {} to deploy".format(name)
        }

    deploy_instances = stack_to_deploy["config"]["instances"]
    provision_tasks = [
        provision_instance(instance_name, instance_details)
        for instance_name, instance_details in deploy_instances.items()
    ]
    provision_results = await asyncio.gather(*provision_tasks)
    for result in provision_results:
        if result[0]:
            stack_to_deploy["instances"][result[1]["instance"].name] = result[1][
                "instance"
            ]
        else:
            print("Failed to provision instance: {}.".format(result[1]["name"]))

    deploy_pools = await stack_to_deploy["config"]["pools"]

    if not await stack_db.update(name, stack_to_deploy):
        return False, {"error": "Failed to update stack: {}".format(name)}
    return True, {"msg": "Stack: {} deployed successfully.".format(name)}
