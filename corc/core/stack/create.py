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


async def create(name, config=None, directory=None):
    response = {}

    if not config:
        config = {}

    config_file = None
    if isinstance(config, str):
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

    stack = {"name": name, "config": {}, "instances": {}}
    # Load the stack configuration file
    if config_file:
        stack_config = await get_stack_config(config_file)
        if not stack_config:
            response["msg"] = "Failed to load the Stack configuration file: {}.".format(
                config_file
            )
            return False, response
    else:
        stack_config = config

    # Extract the instance configurations
    instances_success, instances_response = await get_stack_config_instances(
        stack_config
    )
    if not instances_success:
        return False, instances_response
    stack["config"]["instances"] = instances_response

    stack_id = await stack_db.add(stack)
    if not stack_id:
        response["msg"] = (
            "Failed to save the Stack information to the database: {}".format(
                stack_db.name
            )
        )
        return False, response

    response["id"] = stack_id
    response["stack"] = stack
    response["msg"] = "Created Stack succesfully."
    return True, response
