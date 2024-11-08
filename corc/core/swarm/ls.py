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

from corc.core.defaults import SWARM
from corc.core.swarm.defaults import default_swarm_perstistence_path
from corc.core.storage.dictdatabase import discover_databases, DictDatabase


async def ls(*args, directory=None):
    if not directory:
        directory = default_swarm_perstistence_path
    response = {}

    swarm_db_path = await discover_databases(directory, database_prefix=SWARM)
    if not swarm_db_path:
        response["swarms"] = []
        response["msg"] = "No Swarm Database was found in directory: {}.".format(
            directory
        )
        return True, response

    swarm_db = DictDatabase(SWARM, directory=directory)
    if not await swarm_db.exists():
        response["swarms"] = []
        response["msg"] = "No Swarm Database was found in: {}.".format(
            swarm_db.get_database_path()
        )
        return True, response

    response["swarms"] = await swarm_db.items()
    response["msg"] = "Found swarms."
    return True, response
