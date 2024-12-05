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


async def show(name, directory=None):
    response = {}

    pool_db = DictDatabase(POOL, directory=directory)
    if not await pool_db.exists():
        if not await pool_db.touch():
            response["msg"] = (
                "The Pool database: {} did not exist in directory: {}, and it could not be created.".format(
                    pool_db.name, directory
                )
            )
            return False, response

    pool = await pool_db.get(name)
    if not pool:
        response["msg"] = f"The Pool: {name} does not exist in the database."
        return False, response

    response["pool"] = pool
    response["msg"] = "Pool members."
    return True, response
