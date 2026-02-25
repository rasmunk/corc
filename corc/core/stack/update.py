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
from corc.core.stack.config import get_stack_config, get_stack_config_instances


async def update(stack_id, name=None, config=None, instances=None, directory=None):
    response = {}

    config_file = None
    if config is not None and isinstance(config, str):
        config_file = config

    stack_db = DictDatabase(STACK, directory=directory)
    if not await stack_db.exists():
        if not await stack_db.touch():
            response["msg"] = (
                "The Stack database: {} did not exist in directory: {}, and it could not be created.".format(
                    stack_db.name, directory
                )
            )
            return False, response

    stack_to_update = await stack_db.get(stack_id)
    if not stack_to_update:
        response["msg"] = (
            "Failed to find a Stack inside the database with name: {} to update.".format(
                stack_id
            )
        )
        return False, response

    stack_config = None
    if config is not None and isinstance(config, dict):
        # Assume that a new config dict was passed directly
        stack_config = config

    if config is not None and isinstance(config, str):
        # Assume a path to the config file was given and load it
        stack_config = await get_stack_config(config_file)
        if not stack_config:
            response["msg"] = "Failed to load the Stack configuration file: {}.".format(
                config_file
            )
            return False, response

    new_config_instances = None
    if stack_config is not None:
        # Extract the instance configurations
        config_instances_success, config_instances_response = await get_stack_config_instances(
            stack_config
        )
        if not config_instances_success:
            return False, config_instances_response
        new_config_instances = config_instances_response

    # Update the config instances
    if new_config_instances is not None:
        stack_to_update["config"]["instances"] = new_config_instances

    # Update the instances state
    if instances is not None:
        stack_to_update["instances"] = instances

    # Update the stack name
    if name is not None:
        stack_to_update["name"] = name

    if not await stack_db.update(stack_id, stack_to_update):
        response["msg"] = (
            "Failed to save the updated Stack information to the database: {}".format(
                stack_db.name
            )
        )
        return False, response

    response["msg"] = "The Stack: {} has been updated.".format(stack_id)
    return True, response
