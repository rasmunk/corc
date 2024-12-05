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

from corc.core.defaults import STACK
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.stack.config import (
    get_stack_config,
    get_stack_config_instances,
    get_stack_config_pools,
)


async def update(name, config_file=None, directory=None):
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

    stack_to_update = await stack_db.get(name)
    if not stack_to_update:
        response["msg"] = (
            "Failed to find a Stack inside the database with name: {} to update.".format(
                name
            )
        )
        return False, response

    # Load the architecture file and deploy the stack
    stack_config = await get_stack_config(config_file)
    if not stack_config:
        response["msg"] = "Failed to load the Stack configuration file: {}.".format(
            config_file
        )
        return False, response

    # Extract the pool configurations
    stack_to_update["config"]["pools"] = await get_stack_config_pools(stack_config)

    # Extract the instance configurations
    instances_success, instances_response = await get_stack_config_instances(
        stack_config
    )
    if not instances_success:
        return False, instances_response
    stack_to_update["config"]["instances"] = instances_response

    if not await stack_db.update(name, stack_to_update):
        response["msg"] = (
            "Failed to save the updated Stack information to the database: {}".format(
                stack_db.name
            )
        )
        return False, response

    response["msg"] = "The Stack: {} has been updated.".format(name)
    return True, response
