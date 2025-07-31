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

from corc.core.defaults import PLAN
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.stack.plan.defaults import INITIALIZER, ORCHESTRATOR, CONFIGURER
from corc.core.stack.plan.config import (
    get_plan_config,
    get_component_config,
    validate_plan_component,
)


async def update(plan_id, config=None, directory=None):
    response = {}

    if not config:
        config = {}

    config_file = None
    if isinstance(config, str):
        config_file = config

    plan_db = DictDatabase(PLAN, directory=directory)
    if not await plan_db.exists():
        response["msg"] = (
            "The Plan: {} database does not exist in directory: {}.".format(
                plan_id, directory
            )
        )
        return False, response

    plan_to_update = await plan_db.get(plan_id)
    if not plan_to_update:
        response["msg"] = (
            "Failed to find a Plan inside the database: {} to update.".format(plan_id)
        )
        return False, response

    # Load the plan configuration file
    if config_file:
        plan_config = await get_plan_config(config_file)
        if not plan_config:
            response["msg"] = "Failed to load the Plan configuration file: {}.".format(
                config_file
            )
            return False, response
    else:
        plan_config = config

    for component in [INITIALIZER, ORCHESTRATOR, CONFIGURER]:
        component_config = get_component_config(component, plan_config)
        if component_config:
            # Validate the plan components
            validate_success, validate_response = validate_plan_component(
                component, component_config
            )
            if not validate_success:
                return False, validate_response
            plan_to_update[component] = component_config

    if not await plan_db.update(plan_id, plan_to_update):
        response["msg"] = (
            "Failed to save the updated Plan information: {} to the database: {}".format(
                plan_to_update, plan_db.name
            )
        )
        return False, response

    response["msg"] = "The Plan: {} has been updated.".format(plan_id)
    return True, response
