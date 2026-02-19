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

import asyncio
from corc.core.defaults import STACK
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.helpers import import_from_module
from corc.core.plugins.plugin import discover, import_plugin


async def destroy_instance(instance_id, instance_details):
    plugin_driver = discover(instance_details["provider"]["name"])
    if not plugin_driver:
        return False, {
            "id": instance_id,
            "msg": "Provider: {} is not installed.".format(
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
            "msg": "Failed to load plugin: {}.".format(
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
            "msg": "Failed to create client for provider driver: {}.".format(
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
            "msg": "Provider: {} is not installed.".format(
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
            "msg": "Failed to load plugin: {}.".format(
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
            "msg": "Failed to create client for provider driver: {}.".format(
                instance_details["provider"]["driver"]
            ),
        }

    provider_get_func = import_from_module(
        "{}.{}".format(plugin_driver.module, "get"), "get", "get"
    )
    return await provider_get_func(driver, instance_id)


async def destroy(stack_id, directory=None):
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

    stack = await stack_db.get(stack_id)
    if not stack:
        response["msg"] = "Stack: {} does not exist.".format(stack_id)
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
    remove_errors = []
    # Update the stack config and remove the instances
    for success, details in await asyncio.gather(*remove_tasks):
        if success:
            instance_name = remove_instance_details[details["id"]]["name"]
            stack["instances"].pop(instance_name)
        else:
            remove_errors.append(
                "Failed to shutdown Instance: {}.".format(details["id"])
            )

    if remove_errors:
        response["errors"] = remove_errors
        response["msg"] = "Failed to remove Instances for Stack: {}".format(stack_id)

    # Persist the changes to the stack
    updated = await stack_db.update(stack_id, stack)
    if not updated:
        response["msg"] = "Failed to update Stack: {} after removing Instances".format(
            stack_id
        )
        return False, response

    if not await stack_db.remove(stack_id):
        response["msg"] = "Failed to remove Stack: {}.".format(stack_id)
        return False, response

    if await stack_db.is_empty() and not await stack_db.remove_persistence():
        response["msg"] = "Failed to remove Stack persistence: {}.".format(stack_id)
        return False, response

    response["msg"] = "Stack: {} has been destroyed.".format(stack_id)
    return True, response
