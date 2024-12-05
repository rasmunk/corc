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
from corc.core.orchestration.pool.models import Instance, find_instance_by_name


async def add_instance(pool_name, instance_name, **kwargs):
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

    if find_instance_by_name(pool["instances"], instance_name):
        response["msg"] = "An Instance with name: {} already exists in Pool.".format(
            instance_name
        )
        return False, response

    pool["instances"].append(Instance(instance_name, **kwargs))
    if not await pool_db.update(pool_name, pool):
        response["msg"] = "Failed to update the Pool: {} with a new Instance.".format(
            pool_name
        )
        return

    response["msg"] = "Added Instance with name {} to pool.".format(instance_name)
    return True, response
