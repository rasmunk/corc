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

from corc.core.orchestration.pool.models import Pool


async def show(*args, **kwargs):
    response = {}
    pool = Pool(*args, **kwargs)
    if not await pool.exists():
        response["msg"] = f"Pool does not exist: {pool.name}."
        return False, response

    response["members"] = await pool.items()
    response["msg"] = "Pool members."
    return True, response
