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

from corc.utils.io import load_yaml, exists


async def get_plan_config(config_file):
    # Load the architecture file and deploy the plan
    if not exists(config_file):
        return False
    return load_yaml(config_file)


def get_component_config(component, config):
    return config.get(component, {})


def validate_plan_component(component, config):
    provider = config.get("provider", None)
    if not provider:
        return False, {"msg": "Provider is required for the: {}.".format(component)}

    settings = config.get("settings", None)
    if not settings:
        return False, {"msg": "Settings is required for the: {}.".format(component)}

    return True, {}
