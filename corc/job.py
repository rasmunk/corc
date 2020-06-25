import os

filename = os.path.basename(__file__)
module_name = os.path.splitext(filename)[0]


def run(provider, provider_kwargs={}, action_kwargs={}):
    func_name = "run"
    import_path = "{}.{}.{}".format("corc.providers", provider, module_name)
    module = __import__(import_path, fromlist=[module_name])
    run_func = getattr(module, func_name)
    return run_func(provider_kwargs, **action_kwargs)


def get_results(provider, provider_kwargs={}, action_kwargs={}):
    func_name = "get_results"
    import_path = "{}.{}.{}".format("corc.providers", provider, module_name)
    module = __import__(import_path, fromlist=[module_name])
    run_func = getattr(module, func_name)
    return run_func(provider_kwargs, action_kwargs)


def delete_results(provider, provider_kwargs={}, action_kwargs={}):
    func_name = "delete_results"
    import_path = "{}.{}.{}".format("corc.providers", provider, module_name)
    module = __import__(import_path, fromlist=[module_name])
    run_func = getattr(module, func_name)
    return run_func(provider_kwargs, action_kwargs)


def list_results(provider, provider_kwargs={}, action_kwargs={}):
    func_name = "list_results"
    import_path = "{}.{}.{}".format("corc.providers", provider, module_name)
    module = __import__(import_path, fromlist=[module_name])
    run_func = getattr(module, func_name)
    return run_func(provider_kwargs, action_kwargs)
