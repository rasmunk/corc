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
from corc.core.defaults import STACK, default_persistence_path
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.helpers import import_from_module
from corc.core.plugins.plugin import discover, import_plugin
from corc.core.stack.config import (
    extract_instance_config,
    extract_instance_plan,
    discover_plan,
    prepare_instance_plan,
    prepare_instance,
)


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


async def prepare_instance_config(instance_name, instance_config, directory=None):
    if not directory:
        directory = default_persistence_path

    if "plan" in instance_config:
        success_extract, response_extract = await extract_instance_plan(instance_config)
        if not success_extract:
            return False, {
                "name": instance_name,
                "msg": "Failed to extract the plan from the config: {}.".format(
                    instance_config
                ),
            }

        plan_name = response_extract["plan"]
        success_discover, response_discover = await discover_plan(
            plan_name, directory=directory
        )
        if not success_discover:
            return False, {
                "name": instance_name,
                "msg": "Failed to discover the plan: {}.".format(plan_name),
            }

        plan = response_discover
        success_prepare, response_prepare = await prepare_instance_plan(
            instance_name, instance_config, plan
        )
        if not success_prepare:
            return False, {
                "name": instance_name,
                "msg": "Failed to prepare the instance with config: {} and plan: {}.".format(
                    instance_config, plan
                ),
            }
        instance_config = response_prepare
    else:
        success_prepare, response_prepare = await prepare_instance(
            instance_name, instance_config
        )
        if not success_prepare:
            return False, {
                "name": instance_name,
                "msg": "Failed to prepare the instance with config: {}.".format(
                    instance_config
                ),
            }
        instance_config = response_prepare

    success, response = await extract_instance_config(instance_name, instance_config)
    if not success:
        return False, {
            "name": instance_name,
            "msg": "Failed to extract the instance config: {}.".format(instance_config),
        }

    instance_config = response
    return True, {"name": instance_name, "config": instance_config}


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
                prepare_response["name"],
                prepare_response["config"],
            )
            prepared_instances_configs[instance_name] = instance_details
        else:
            print(
                "Failed to prepare instance: {} - {}".format(
                    prepare_response["name"], prepare_response["msg"]
                )
            )

    provision_tasks = [
        provision_instance(instance_name, instance_details)
        for instance_name, instance_details in prepared_instances_configs.items()
    ]
    for provision_success, provision_response in await asyncio.gather(*provision_tasks):
        if provision_success:
            stack_to_deploy["instances"][provision_response["instance"].name] = (
                provision_response["instance"]
            )
        else:
            print(
                "Failed to provision instance: {} - {}".format(
                    provision_response["name"], provision_response["msg"]
                )
            )

    if not await stack_db.update(name, stack_to_deploy):
        response["msg"] = "Failed to update stack: {}.".format(name)
        return False, response

    response["msg"] = "Stack: {} deployed successfully.".format(name)
    return True, response
