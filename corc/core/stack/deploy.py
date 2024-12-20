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
from corc.core.plugins.plugin import (
    import_plugin,
    load,
    PLUGIN_ENTRYPOINT_BASE,
    get_plugin_module_path_and_name,
)
from corc.core.stack.config import (
    get_instance_config_plan_name,
    get_plan,
    prepare_instance_plan,
    prepare_instance,
)
from corc.core.stack.plan.defaults import INITIALIZER, ORCHESTRATOR, CONFIGURER


def init_plugin(plugin_name, plugin_type):
    plugin = load(plugin_name, plugin_type=plugin_type)
    if not plugin:
        return False, {
            "msg": "Plugin: {} could not be loaded.".format(plugin_name),
        }

    return True, plugin


def init_plugin_driver(plugin_name, driver_name, *args, **kwargs):
    driver_client_func = import_from_module(
        "{}.{}".format(plugin_name, "client"), "client", "new_client"
    )
    driver = driver_client_func(driver_name, *args, **kwargs)
    if not driver:
        return False, {
            "msg": "Failed to create client provider driver: {}.".format(driver_name),
        }

    return True, driver


def init_plugin_and_driver(
    plugin_name, plugin_type, driver_name, *driver_args, **driver_kwargs
):
    init_plugin_success, init_plugin_response = init_plugin(plugin_name, plugin_type)
    if not init_plugin_success:
        return False, init_plugin_response

    init_driver_success, init_driver_response = init_plugin_driver(
        plugin_name, driver_name, *driver_args, **driver_kwargs
    )

    return True, {"plugin": init_plugin_response, "driver": init_driver_response}


async def initialize_instance(instance_name, initializer_config):
    init_plugin_success, init_plugin_response = init_plugin(
        initializer_config["provider"]["name"], INITIALIZER
    )
    if not init_plugin_success:
        return False, {"name": instance_name, "msg": init_plugin_response["msg"]}

    initializer_module_path, initializer_module_function_name = (
        get_plugin_module_path_and_name(
            initializer_config["provider"]["name"],
            plugin_module_entrypoint="{}.{}".format(
                PLUGIN_ENTRYPOINT_BASE, INITIALIZER
            ),
        )
    )
    if not initializer_module_path:
        return False, {
            "name": instance_name,
            "msg": "Failed to find the initializer module path for plugin: {}.".format(
                initializer_config["provider"]["name"]
            ),
        }

    if not initializer_module_function_name:
        return False, {
            "name": instance_name,
            "msg": "Failed to find the initializer module function name for plugin: {}.".format(
                initializer_config["provider"]["name"]
            ),
        }

    imported_initializer_module = import_plugin(
        initializer_module_path, return_module=True
    )

    initializer_function = getattr(
        imported_initializer_module, initializer_module_function_name
    )
    return await initializer_function(initializer_config)


async def configure_instance(instance_name, configurer_config):
    init_plugin_success, init_plugin_response = init_plugin(
        configurer_config["provider"]["name"], CONFIGURER
    )
    if not init_plugin_success:
        return False, {"name": instance_name, "msg": init_plugin_response["msg"]}

    configurer_module_path, configurer_module_function_name = (
        get_plugin_module_path_and_name(
            configurer_config["provider"]["name"],
            plugin_module_entrypoint="{}.{}".format(PLUGIN_ENTRYPOINT_BASE, CONFIGURER),
        )
    )

    if not configurer_module_path:
        return False, {
            "name": instance_name,
            "msg": "Failed to find the configurer module path for plugin: {}.".format(
                configurer_config["provider"]["name"]
            ),
        }

    if not configurer_module_function_name:
        return False, {
            "name": instance_name,
            "msg": "Failed to find the configurer module function name for plugin: {}.".format(
                configurer_config["provider"]["name"]
            ),
        }

    imported_configurer_module = import_plugin(
        configurer_module_path, return_module=True
    )

    configurer_function = getattr(
        imported_configurer_module, configurer_module_function_name
    )
    return await configurer_function(configurer_config)


async def provision_instance(instance_name, orchestrator_config):
    init_success, response = init_plugin_and_driver(
        orchestrator_config["provider"]["name"],
        ORCHESTRATOR,
        orchestrator_config["provider"]["driver"],
        *orchestrator_config["provider"].get("args", []),
        **orchestrator_config["provider"].get("kwargs", {})
    )
    if not init_success:
        return False, {"name": instance_name, "msg": response["msg"]}

    plugin = response["plugin"]
    driver = response["driver"]

    provider_create_func = import_from_module(
        "{}.{}".format(plugin.module, "create"), "create", "create"
    )
    return await provider_create_func(
        driver,
        *orchestrator_config["settings"]["args"],
        **orchestrator_config["settings"]["kwargs"]
    )


async def prepare_stack_instance(instance_name, instance_config, directory=None):
    if not directory:
        directory = default_persistence_path

    if "plan" in instance_config:
        get_name_success, get_name_response = await get_instance_config_plan_name(
            instance_config
        )
        if not get_name_success:
            return False, {
                "name": instance_name,
                "msg": "Failed to extract the plan from the config: {}.".format(
                    instance_config
                ),
            }

        plan_name = get_name_response["name"]
        get_plan_success, get_plan_response = await get_plan(
            plan_name, directory=directory
        )

        if not get_plan_success:
            return False, {
                "name": instance_name,
                "msg": "Failed to discover the plan: {}.".format(plan_name),
            }

        plan = get_plan_response["plan"]
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
        prepare_stack_instance(instance_name, instance_details, directory=directory)
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

    initialize_tasks = [
        initialize_instance(instance_name, instance_details[INITIALIZER])
        for instance_name, instance_details in prepared_instances_configs.items()
        if INITIALIZER in instance_details
    ]

    for initialize_success, initialize_response in await asyncio.gather(
        *initialize_tasks
    ):
        if not initialize_success:
            print(
                "Failed to initialize instance: {} - {}".format(
                    initialize_response["name"], initialize_response["msg"]
                )
            )

    provision_tasks = [
        provision_instance(instance_name, instance_details[ORCHESTRATOR])
        for instance_name, instance_details in prepared_instances_configs.items()
        if ORCHESTRATOR in instance_details
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

    configurer_tasks = [
        configure_instance(instance_name, instance_details[CONFIGURER])
        for instance_name, instance_details in prepared_instances_configs.items()
        if CONFIGURER in instance_details
    ]
    for configurer_success, configurer_response in await asyncio.gather(
        *configurer_tasks
    ):
        if not configurer_success:
            print(
                "Failed to configure instance: {} - {}".format(
                    configurer_response["name"], configurer_response["msg"]
                )
            )

    if not await stack_db.update(name, stack_to_deploy):
        response["msg"] = "Failed to update stack: {}.".format(name)
        return False, response

    response["msg"] = "Stack: {} deployed successfully.".format(name)
    return True, response
