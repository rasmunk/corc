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


async def ls(*args, directory=None):
    response = {}

    plan_db = DictDatabase(PLAN, directory=directory)
    if not await plan_db.exists():
        response["msg"] = "The Plan database {} does not exist.".format(plan_db.name)
        return False, response

    plans = await plan_db.items()
    if not plans:
        response["plans"] = []
        response["msg"] = "No plans found."
        return True, response

    response["plans"] = plans
    response["msg"] = "Found plans."
    return True, response
