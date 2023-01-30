from libcloud.compute.providers import get_driver
from corc.helpers import import_from_module


def discover_apache_driver(provider):
    return get_driver(provider)


def discover_apache_driver_options(provider):
    loader = import_from_module(
        "corc.providers.apache.config_{}".format(provider),
        "config_{}".format(provider),
        "load_driver_options",
    )
    return loader


def new_apache_client(provider, provider_kwargs, **kwargs):
    # Discover driver
    driver = discover_apache_driver(provider)
    options_loader = discover_apache_driver_options(provider)
    driver_args, driver_kwargs = options_loader(provider, provider_kwargs, **kwargs)
    return driver(*driver_args, **driver_kwargs)
