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

import jinja2
from corc.core.defaults import default_persistence_path
from corc.utils.io import load_yaml, exists
from corc.core.stack.plan.show import show


async def get_stack_config(config_file):
    # Load the architecture file and deploy the stack
    if not exists(config_file):
        return False
    return load_yaml(config_file)


async def extract_instance_config(instance_name, instance_kwargs):
    provider = instance_kwargs.get("provider", None)
    if not provider:
        return False, {
            "msg": "Provider for node: {} is required.".format(instance_name)
        }

    instance_settings = instance_kwargs.get("settings", None)
    if not instance_settings:
        return False, {
            "msg": "Settings for node: {} are required.".format(instance_name)
        }

    return True, {
        "provider": provider,
        "settings": instance_settings,
    }


async def recursively_prepare_instance_config(template_vars, instance_config):
    output_dict = {}
    # TODO, augment to support recursive templating
    if isinstance(instance_config, list):
        templated_list = []
        for config in instance_config:
            templated_list.append(
                await recursively_prepare_instance_config(template_vars, config)
            )
        return templated_list
    elif isinstance(instance_config, dict):
        for key, value in instance_config.items():
            output_dict[key] = await recursively_prepare_instance_config(
                template_vars, value
            )
    elif isinstance(instance_config, str):
        environment = jinja2.Environment()
        template = environment.from_string(instance_config)
        return template.render(template_vars)
    elif isinstance(instance_config, (int, float, bytes)):
        return instance_config
    return output_dict


async def get_stack_config_instances(stack_config):
    deploy_instance_configs = {}
    for instance_name, instance_kwargs in stack_config.get("instances", {}).items():
        if "[" in instance_name and "]" in instance_name:
            # Node range defined, unroll list
            start_string_index = instance_name.index("[")
            stop_string_index = instance_name.index("]")

            range_numbers = [
                int(number)
                for number in instance_name[
                    start_string_index + 1 : stop_string_index
                ].split("-")
            ]
            unrolled_instances = [
                "instance{:02d}".format(i)
                for i in range(range_numbers[0], range_numbers[1] + 1)
            ]

            for unrolled_instance in unrolled_instances:
                success, response = await extract_instance_config(
                    unrolled_instance, instance_kwargs
                )
                if not success:
                    return False, response
                instance_config = response
                instance_template_values = {
                    "instance": {
                        "name": unrolled_instance,
                    }
                }
                templated_instance_config = await recursively_prepare_instance_config(
                    instance_template_values, instance_config
                )
                deploy_instance_configs[unrolled_instance] = templated_instance_config
        else:
            success, response = await extract_instance_config(
                instance_name, instance_kwargs
            )
            if not success:
                return False, response
            instance_config = response
            instance_template_values = {
                "instance": {
                    "name": instance_name,
                }
            }
            templated_instance_config = await recursively_prepare_instance_config(
                instance_template_values, instance_config
            )
            deploy_instance_configs[instance_name] = templated_instance_config
    return True, deploy_instance_configs


async def get_stack_config_pools(stack_config):
    return stack_config.get("pools", {})


async def extract_instance_plan(instance_name, instance_config):
    return True, instance_config.get("plan", {})


async def discover_plan(plan_name, directory=None):
    if not directory:
        directory = default_persistence_path

    success, response = await show(plan_name, directory)
    if not success:
        return False, response["msg"]
    return True, response["plan"]


async def prepare_instance_plan(plan):
    initializer = plan.get("initializer", {})
    orchestrator = plan.get("orchestrator", {})
    configurer = plan.get("configurer", {})

    # TODO, recuresively expand the plan
    recursively_prepare_instance_config()

    return True, {
        "initializer": initializer,
        "orchestrator": orchestrator,
        "configurer": configurer,
    }


async def prepare_instance_config(instance_name, instance_config, directory=None):
    if not directory:
        directory = default_persistence_path

    if "plan" in instance_config:
        success_extract, response_extract = await extract_instance_plan(
            instance_name, instance_config
        )
        if not success_extract:
            return False, response_extract
        success_discover, response_discover = await discover_plan(
            response_extract, directory=directory
        )
        if not success_discover:
            return False, response_discover
        plan = response_discover

        success_prepare, response_prepare = await prepare_instance_plan(plan)
        if not success_prepare:
            return False, response_prepare
        instance_config = response_prepare

    success, response = await extract_instance_config(instance_name, instance_config)
    if not success:
        return False, response

    instance_config = response
    return True, {instance_name: instance_config}
