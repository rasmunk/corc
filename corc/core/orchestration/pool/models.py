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

import copy
import uuid


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

    def __eq__(self, other):
        if not isinstance(other, Instance):
            return NotImplemented
        return (
            self.id == other.id
            and self.name == self.name
            and self.state == other.state
            and self.config == other.config
        )

    def __str__(self):
        return "Instance id: {} name: {}, state: {}, config: {}".format(
            self.id, self.name, self.state, self.config
        )

    def asdict(self):
        return {
            "name": self.name,
            "state": self.state,
            "config": self.config,
        }


def remove_instance_from_list(instances, instance_id):
    copy_instances_list = copy.deepcopy(instances)
    for instance in copy_instances_list:
        if instance.id == instance_id:
            try:
                index = copy_instances_list.index(instance)
                del copy_instances_list[index]
            except ValueError:
                return False
    return copy_instances_list


def find_instance_by_id(instances, instance_id):
    for instance in instances:
        if instance.id == instance_id:
            return instance
    return None


def find_instance_by_name(instances, instance_name):
    for instance in instances:
        if instance.name == instance_name:
            return instance
    return None
