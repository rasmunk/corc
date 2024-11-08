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

import uuid
from corc.core.storage.dictdatabase import DictDatabase


class Pool(DictDatabase):
    def __init__(self, name, **kwargs):
        # The name of the pool is equal to the
        # database name
        super().__init__(name, **kwargs)


class Instance:
    def __init__(self, name, **kwargs):
        self.id = str(uuid.uuid4())
        self.name = name
        self.state = None
        self.config = kwargs

    def print_state(self):
        print(
            "Instance name: {}, state: {}, config: {}".format(
                self.name, self.state, self.config
            )
        )

    def __str__(self):
        return "Instance name: {}, state: {}, config: {}".format(
            self.name, self.state, self.config
        )

    def asdict(self):
        return {
            "name": self.name,
            "state": self.state,
            "config": self.config,
        }
