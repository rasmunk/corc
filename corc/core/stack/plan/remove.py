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


async def remove(plan_id, directory=None):
    response = {}

    plan_db = DictDatabase(PLAN, directory=directory)
    if not await plan_db.exists():
        if not await plan_db.touch():
            response["msg"] = (
                f"The Plan database: {plan_db.name} did not exist in directory: {directory}, and it could not be created."
            )
            return False, response

    if not await plan_db.get(plan_id):
        response["msg"] = f"The Plan: {plan_id} does not exist in the database."
        return True, response

    if not await plan_db.remove(plan_id):
        response["msg"] = f"Failed to remove the Plan: {plan_id}."
        return False, response

    response["msg"] = f"Removed plan: {plan_id}."
    return True, response
