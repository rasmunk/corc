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

from corc.core.defaults import POOL
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.orchestration.pool.models import (
    find_instance_by_id,
    remove_instance_from_list,
)


async def remove_instance(pool_name, node_id, **kwargs):
    response = {}

    directory = kwargs.get("directory", None)
    pool_db = DictDatabase(POOL, directory=directory)
    if not await pool_db.exists():
        if not await pool_db.touch():
            response["msg"] = (
                "The Pool database: {} did not exist in directory: {}, and it could not be created.".format(
                    pool_db.name, directory
                )
            )
            return False, response

    pool = await pool_db.get(pool_name)
    if not pool:
        response["msg"] = "The Pool: {} does not exist in the database.".format(
            pool_name
        )
        return False, response

    if not find_instance_by_id(pool["instances"], node_id):
        response["msg"] = "An Instance with the id: {} is not in the Pool.".format(
            node_id
        )
        return False, response

    updated_instances = remove_instance_from_list(pool["instances"], node_id)
    if not isinstance(updated_instances, list):
        response["msg"] = "Failed to remove Instance: {} from Pool.".format(node_id)
        return False, response

    pool["instances"] = updated_instances
    if not await pool_db.update(pool_name, pool):
        response["msg"] = (
            "Failed to save the Pool: {} after the Instance with id: {} was removed.".format(
                pool_name, node_id
            )
        )
        return False, response

    response["msg"] = "Removed Instance: {} from Pool.".format(node_id)
    return True, response
