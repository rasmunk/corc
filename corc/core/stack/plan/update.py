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
from corc.core.stack.plan.config import (
    get_plan_config,
    get_plan_initalizers,
    get_plan_orchestrators,
    get_plan_configurers,
)


async def update(name, config_file=None, directory=None):
    response = {}

    plan_db = DictDatabase(PLAN, directory=directory)
    if not await plan_db.exists():
        response["msg"] = (
            "The Plan: {} database does not exist in directory: {}.".format(
                name, directory
            )
        )
        return False, response

    plan_to_update = await plan_db.get(name)
    if not plan_to_update:
        response["msg"] = (
            "Failed to find a Plan inside the database with name: {} to update.".format(
                name
            )
        )
        return False, response

    # Load the architecture file and deploy the plan
    plan_config = await get_plan_config(config_file)
    if not plan_config:
        response["msg"] = "Failed to load the Plan configuration file: {}.".format(
            config_file
        )
        return False, response

    # Extract the pool configurations
    plan_to_update["initializers"] = await get_plan_initalizers(plan_config)
    plan_to_update["orchestrators"] = await get_plan_orchestrators(plan_config)
    plan_to_update["configurers"] = await get_plan_configurers(plan_config)

    if not await plan_db.update(name, plan_to_update):
        response["msg"] = (
            "Failed to save the updated Plan information: {} to the database: {}".format(
                plan_to_update, plan_db.name
            )
        )
        return False, response

    response["msg"] = "The Plan: {} has been updated.".format(name)
    return True, response
