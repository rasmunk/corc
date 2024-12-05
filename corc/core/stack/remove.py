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


async def remove(name, directory=None):
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

    if not await stack_db.get(name):
        response["msg"] = f"The Stack: {name} does not exist in the database."
        return True, response

    if not await stack_db.remove(name):
        response["msg"] = f"Failed to remove the Stack: {name}."
        return False, response

    response["msg"] = f"Removed Stack: {name}."
    return True, response
