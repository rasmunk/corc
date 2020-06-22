import os
import corc.providers as providers
from corc.providers.oci.job import (
    run as oci_run,
    get_results as oci_get_results,
    delete_results as oci_delete_results,
    list_results as oci_list_results,
)

filename = os.path.basename(__file__)
module_name = os.path.splitext(filename)[0]


def run(provider, provider_kwargs={}, action_kwargs={}):
    func_name = "run"
    import_path = "{}.{}.{}".format("corc.providers", provider, module_name)
    module = __import__(import_path, fromlist=[module_name])
    run_func = getattr(module, func_name)
    return run_func(provider_kwargs, **action_kwargs)


def get_results(provider, **kwargs):
    func_name = "get_results"
    import_path = "{}.{}.{}".format("corc.providers", provider, module_name)
    module = __import__(import_path, fromlist=[module_name])
    run_func = getattr(module, func_name)
    return run_func(provider_kwargs, action_kwargs)


def delete_results(provider, **kwargs):
    func_name = "delete_results"
    import_path = "{}.{}.{}".format("corc.providers", provider, module_name)
    module = __import__(import_path, fromlist=[module_name])
    run_func = getattr(module, func_name)
    return run_func(provider_kwargs, action_kwargs)


def list_results(provider, **kwargs):
    func_name = "list_results"
    import_path = "{}.{}.{}".format("corc.providers", provider, module_name)
    module = __import__(import_path, fromlist=[module_name])
    run_func = getattr(module, func_name)
    return run_func(provider_kwargs, action_kwargs)
