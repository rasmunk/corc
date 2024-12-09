# Copyright (C) 2024  rasmunk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# Description: Deploy the stack
import asyncio
from corc.core.defaults import STACK
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.helpers import import_from_module
from corc.core.plugins.plugin import discover, import_plugin
from corc.core.stack.config import prepare_instance_config


async def provision_instance(instance_name, instance_details):
    plugin_driver = discover(instance_details["provider"]["name"])
    if not plugin_driver:
        return False, {
            "name": instance_name,
            "msg": "Provider: {} is not installed.".format(
                instance_details["provider"]["name"]
            ),
        }

    driver_args = []
    if "args" in instance_details["provider"] and instance_details["provider"]["args"]:
        driver_args = instance_details["provider"]["args"]

    driver_kwargs = {}
    if (
        "kwargs" in instance_details["provider"]
        and instance_details["provider"]["kwargs"]
    ):
        driver_kwargs = instance_details["provider"]["kwargs"]

    plugin_module = import_plugin(plugin_driver.name, return_module=True)
    if not plugin_module:
        return False, {
            "name": instance_name,
            "msg": "Failed to load plugin: {}.".format(
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
            "msg": "Failed to create client for provider driver: {}.".format(
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


async def deploy(name, directory=None):
    response = {}

    stack_db = DictDatabase(STACK, directory=directory)
    if not await stack_db.exists():
        if not await stack_db.touch():
            response["msg"] = (
                "The Stack database: {} did not exist in directory: {}, and it could not be created.".format(
                    stack_db.name, directory
                )
            )
            return False, response

    stack_to_deploy = await stack_db.get(name)
    if not stack_to_deploy:
        response["msg"] = "Failed to find a Stack with name: {} to deploy".format(name)
        return False, response

    deploy_instances = stack_to_deploy["config"]["instances"]
    prepared_instances_configs = {}

    prepare_configs_tasks = [
        prepare_instance_config(instance_name, instance_details, directory=directory)
        for instance_name, instance_details in deploy_instances.items()
    ]

    for prepare_success, prepare_response in await asyncio.gather(
        *prepare_configs_tasks
    ):
        if prepare_success:
            instance_name, instance_details = (
                prepare_response["instance_name"],
                prepare_response["instance_config"],
            )
            prepared_instances_configs[instance_name] = instance_details
        else:
            print(
                "Failed to prepare instance: {} response: {}.".format(
                    prepare_success, prepare_response
                )
            )

    print("Prepared instances configs: {}".format(prepared_instances_configs))
    provision_tasks = [
        provision_instance(instance_name, instance_details)
        for instance_name, instance_details in prepared_instances_configs.items()
    ]
    for success, details in await asyncio.gather(*provision_tasks):
        if success:
            stack_to_deploy["instances"][details["instance"].name] = details["instance"]
        else:
            print("Failed to provision instance: {}.".format(details["name"]))

    if not await stack_db.update(name, stack_to_deploy):
        response["msg"] = "Failed to update stack: {}.".format(name)
        return False, response

    response["msg"] = "Stack: {} deployed successfully.".format(name)
    return True, response
