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
import errno
import inspect
import os
from concurrent.futures.process import ProcessPoolExecutor
from corc.utils.format import error_print
from corc.core.defaults import STACK, default_persistence_path, INITIALIZER, CONFIGURER
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.helpers import import_from_module
from corc.core.plugins.plugin import (
    import_plugin,
    load,
    PLUGIN_ENTRYPOINT_BASE,
    get_plugin_module_path_and_func,
)
from corc.core.stack.config import (
    get_instance_config_plan_name,
    get_plan,
    prepare_instance_plan,
    prepare_instance,
)
from corc.core.stack.plan.defaults import ORCHESTRATOR


def init_plugin(plugin_name, plugin_type):
    plugin = load(plugin_name)
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


def interpret_plugin_response(plugin_type, plugin_return_code, plugin_response):
    if isinstance(plugin_return_code, bool):
        if plugin_return_code:
            return True, plugin_response
        else:
            return False, "Failed executing plugin type: {} response: {}".format(
                plugin_type, plugin_response
            )

    if isinstance(plugin_return_code, int):
        if plugin_return_code == 0:
            return True, plugin_response

        if plugin_return_code in errno.errorcode:
            return (
                False,
                "Failed executing plugin type: {} return code: {}, response: {} - error {}".format(
                    plugin_type,
                    plugin_return_code,
                    plugin_response,
                    errno.errorcode[plugin_return_code],
                ),
            )
        else:
            return (
                False,
                "Failed executing plugin type: {} return code: {}, response: {}".format(
                    plugin_type, plugin_return_code, plugin_response
                ),
            )
    return False, "Failed to interpret plugin result type: {} response: {}".format(
        plugin_type, plugin_response
    )


async def initialize_instance(instance_name, initializer_config):
    init_plugin_success, init_plugin_response = init_plugin(
        initializer_config["provider"]["name"], INITIALIZER
    )
    if not init_plugin_success:
        return False, {"name": instance_name, "msg": init_plugin_response["msg"]}

    initializer_module_path, initializer_module_function_name = (
        get_plugin_module_path_and_func(
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
    if inspect.iscoroutinefunction(initializer_function):
        return True, {
            "name": instance_name,
            "result": await initializer_function(
                *initializer_config["settings"]["args"],
                **initializer_config["settings"]["kwargs"],
            ),
        }
    return True, {
        "name": instance_name,
        "result": initializer_function(
            *initializer_config["settings"]["args"],
            **initializer_config["settings"]["kwargs"],
        ),
    }


def configure_instance(instance_name, configurer_config):
    init_plugin_success, init_plugin_response = init_plugin(
        configurer_config["provider"]["name"], CONFIGURER
    )
    if not init_plugin_success:
        return False, {"name": instance_name, "msg": init_plugin_response["msg"]}

    configurer_module_path, configurer_module_function_name = (
        get_plugin_module_path_and_func(
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
    if inspect.iscoroutinefunction(configurer_function):
        return True, {
            "name": instance_name,
            # Note, since this function is executed as a synchronous blocking process
            # we can't return an coroutine object that can't be serialized
            # Therefore we run a returned coroutine function synchronously via asyncio.run
            "result": asyncio.run(
                configurer_function(
                    *configurer_config["settings"].get("args", []),
                    **configurer_config["settings"].get("kwargs", {}),
                )
            ),
        }
    return True, {
        "name": instance_name,
        "result": configurer_function(
            *configurer_config["settings"].get("args", []),
            **configurer_config["settings"].get("kwargs", {}),
        ),
    }


async def provision_instance(instance_name, orchestrator_config):
    init_success, response = init_plugin_and_driver(
        orchestrator_config["provider"]["name"],
        ORCHESTRATOR,
        orchestrator_config["provider"]["driver"],
        *orchestrator_config["provider"].get("args", []),
        **orchestrator_config["provider"].get("kwargs", {}),
    )
    if not init_success:
        return False, {"name": instance_name, "msg": response["msg"]}

    plugin = response["plugin"]
    driver = response["driver"]

    provider_create_func = import_from_module(
        "{}.{}".format(plugin.module, "create"), "create", "create"
    )
    if inspect.iscoroutinefunction(provider_create_func):
        return True, {
            "name": instance_name,
            "result": await provider_create_func(
                driver,
                *orchestrator_config["settings"]["args"],
                **orchestrator_config["settings"]["kwargs"],
            ),
        }
    return True, {
        "name": instance_name,
        "result": provider_create_func(
            driver,
            *orchestrator_config["settings"]["args"],
            **orchestrator_config["settings"]["kwargs"],
        ),
    }


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
                "msg": "Failed to discover the plan: {}, error: {}".format(plan_name, get_plan_response["msg"]),
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


async def deploy(stack_id, directory=None):
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

    stack_to_deploy = await stack_db.get(stack_id)
    if not stack_to_deploy:
        response["msg"] = "Failed to find a Stack: {} to deploy".format(stack_id)
        return False, response

    deploy_instances = stack_to_deploy["config"]["instances"]

    # Prepare instances
    prepared_instances_configs = {}
    prepare_configs_tasks = [
        prepare_stack_instance(instance_name, instance_details, directory=directory)
        for instance_name, instance_details in deploy_instances.items()
    ]

    prepare_errors = []
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
            prepare_errors.append(
                "Failed to prepare instance: {} - {}".format(
                    prepare_response["name"], prepare_response["msg"]
                )
            )

    if prepare_errors:
        response["errors"] = prepare_errors
        response["msg"] = "Failed to prepare instance configurations for deployment"
        return False, response

    # Initialize instances
    initialize_tasks = [
        initialize_instance(instance_name, instance_details[INITIALIZER])
        for instance_name, instance_details in prepared_instances_configs.items()
        if INITIALIZER in instance_details
    ]

    initialize_errors = []
    for initialize_success, initialize_response in await asyncio.gather(
        *initialize_tasks
    ):
        if initialize_success:
            plugin_result = initialize_response.get("result", {})
            if plugin_result:
                plugin_return_code, plugin_response = plugin_result[0], plugin_result[1]
                plugin_success, parsed_response = interpret_plugin_response(
                    INITIALIZER, plugin_return_code, plugin_response
                )
                if not plugin_success:
                    error_print(parsed_response)
                else:
                    stack_to_deploy["instances"][initialize_response["name"]] = {
                        "plugin_response": parsed_response,
                        "initialized": True,
                        "configured": False,
                    }
                    if not await stack_db.update(stack_id, stack_to_deploy):
                        response["msg"] = "Failed to update stack: {}.".format(stack_id)
                        return False, response
            else:
                initialize_errors.append(
                    "The {} plugin did not respond with any result for instance: {}".format(
                        INITIALIZER, initialize_response["name"]
                    )
                )
        else:
            initialize_errors.append(
                "Failed to {} instance: {} - {}".format(
                    INITIALIZER, initialize_response["name"], initialize_response["msg"]
                )
            )

    if initialize_errors:
        response["errors"] = initialize_errors
        response["msg"] = "Failed to initialize instances for deployment"
        return False, response

    loop = asyncio.get_running_loop()
    configurer_tasks = []
    # TODO, allow user to set the max_workers
    with ProcessPoolExecutor(max_workers=int(os.cpu_count() / 4)) as executor:
        for instance_name, instance_details in prepared_instances_configs.items():
            if (
                CONFIGURER in instance_details
                and instance_name in stack_to_deploy["instances"]
                and stack_to_deploy["instances"][instance_name].get(
                    "initialized", False
                )
                and not stack_to_deploy["instances"][instance_name].get(
                    "configured", False
                )
            ):
                configurer_tasks.append(
                    loop.run_in_executor(
                        executor,
                        configure_instance,
                        instance_name,
                        instance_details[CONFIGURER],
                    )
                )

    configure_errors = []
    for configurer_success, configurer_response in await asyncio.gather(
        *configurer_tasks
    ):
        if configurer_success:
            plugin_result = configurer_response.get("result", {})
            if plugin_result:
                plugin_return_code, plugin_response = (
                    plugin_result[0],
                    plugin_result[1],
                )
                plugin_success, parsed_response = interpret_plugin_response(
                    CONFIGURER, plugin_return_code, plugin_response
                )
                if not plugin_success:
                    error_print(parsed_response)
                else:
                    stack_to_deploy["instances"][configurer_response["name"]].update(
                        {
                            "plugin_response": parsed_response,
                            "configured": True,
                        }
                    )

                    if not await stack_db.update(stack_id, stack_to_deploy):
                        response["msg"] = "Failed to update stack: {}.".format(stack_id)
                        return False, response
            else:
                configure_errors.append(
                    "The {} plugin did not respond with any result for instance: {}".format(
                        CONFIGURER, configurer_response["name"]
                    )
                )
        else:
            configure_errors.append(
                "Failed to {} instance: {} - {}".format(
                    CONFIGURER,
                    configurer_response["name"],
                    configurer_response["msg"],
                )
            )

    if configure_errors:
        response["errors"] = configure_errors
        response["msg"] = "Failed to configure instances for deployment"
        return False, response

    provision_tasks = [
        provision_instance(instance_name, instance_details[ORCHESTRATOR])
        for instance_name, instance_details in prepared_instances_configs.items()
        if ORCHESTRATOR in instance_details
        and instance_name in stack_to_deploy["instances"]
        and stack_to_deploy["instances"][instance_name].get("initialized", False)
        and not stack_to_deploy["instances"][instance_name].get("provisioned", False)
    ]
    provision_errors = []
    for provision_success, provision_response in await asyncio.gather(*provision_tasks):
        if provision_success:
            plugin_result = provision_response.get("result", {})
            if plugin_result:
                plugin_return_code, plugin_response = plugin_result[0], plugin_result[1]
                plugin_success, parsed_response = interpret_plugin_response(
                    ORCHESTRATOR, plugin_return_code, plugin_response
                )
                if not plugin_success:
                    error_print(parsed_response)
                else:
                    stack_to_deploy["instances"][provision_response["name"]].update(
                        {
                            "plugin_response": parsed_response,
                            "provisioned": True,
                        }
                    )
                    if not await stack_db.update(stack_id, stack_to_deploy):
                        provision_errors.append(
                            "Failed to update Stack: {}.".format(stack_id)
                        )
            else:
                provision_errors.append(
                    "The {} plugin did not respond with any result for instance: {}".format(
                        ORCHESTRATOR, provision_response["name"]
                    )
                )
        else:
            provision_errors.append(
                "Failed to {} instance: {} - {}".format(
                    ORCHESTRATOR, provision_response["name"], provision_response["msg"]
                )
            )
    if provision_errors:
        response["errors"] = provision_errors
        response["msg"] = "Failed to provision instances for deployment"
        return False, response

    if not await stack_db.update(stack_id, stack_to_deploy):
        response["msg"] = "Failed to update Stack: {}.".format(stack_id)
        return False, response

    response["msg"] = "Stack: {} deployed successfully.".format(stack_id)
    return True, response
