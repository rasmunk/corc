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

from corc.core.defaults import PACKAGE_NAME
from corc.core.config import (
    config_exists,
    get_config_path,
    load_config,
    save_config,
    generate_default_config,
)
from corc.core.providers.config import generate_config, valid_config


def prepare_config(provider, provider_kwargs, **kwargs):
    # Expects that the default corc config is present
    config = {provider: {}}
    config[provider].update(provider_kwargs)
    config = generate_config(provider, **kwargs)
    if not valid_config(provider, config, verbose=True):
        return False
    return config


def prepare_provider_config(provider, provider_kwargs, **kwargs):
    return prepare_config(provider, provider_kwargs, **kwargs)


def init_config(provider, provider_kwargs, config=None, **kwargs):
    path = get_config_path()
    if config and "path" in config:
        path = config["path"]

    response = {}
    provider_config = prepare_provider_config(provider, provider_kwargs, **kwargs)
    if not provider_config:
        response["msg"] = "Failed to generate the provider config for: {}".format(
            provider
        )
        return False, response

    # If no config exists -> create it
    _config = {}
    if not config_exists(path=path):
        _config = generate_default_config()
        save_config(_config, path=path)
    else:
        _config = load_config(path=path)

    if not config_exists(path=path):
        response["msg"] = "Failed to find a config"
        return False, response

    # Update with user arguments
    _config[PACKAGE_NAME]["providers"].update(provider_config)

    if not save_config(_config, path=path):
        response["msg"] = "Failed to save new config"
        return False, response

    if not valid_config(provider, _config, verbose=True):
        response["msg"] = "The generated config is invalid"
        return False, response

    response["msg"] = "Generated a new configuration"
    return True, response
