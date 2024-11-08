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

from corc.core.defaults import PROVIDERS, DEFAULT_PROVIDER


def select_provider(provider_kwargs=None, default_fallback=False, verbose=False):
    if not provider_kwargs:
        return False

    # Find the activated one
    selected_provider = [
        provider
        for provider in PROVIDERS
        if provider in provider_kwargs and provider_kwargs[provider]
    ]

    if not selected_provider and default_fallback:
        return DEFAULT_PROVIDER

    if not selected_provider and not default_fallback:
        if verbose:
            print("A least a single provider must be set: {}".format(provider_kwargs))
        return False

    if len(selected_provider) > 1:
        if verbose:
            print(
                "Only a single provider must be selected, you selected: {}".format(
                    selected_provider
                )
            )
            return False

    provider = selected_provider[0]
    if provider not in PROVIDERS:
        return False

    # Return the
    return provider
