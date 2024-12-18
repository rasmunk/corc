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

from corc.core.defaults import CONFIGURER
from corc.core.plugins.storage import install


async def add_provider(provider_name):
    """Add a particular provider to corc."""
    # Make the provider configuration directory
    installed = install(CONFIGURER, provider_name)
    if not installed:
        return False, {"msg": "Failed to add the provider: {}".format(provider_name)}
    return True, {"msg": "Added the provider: {}".format(provider_name)}