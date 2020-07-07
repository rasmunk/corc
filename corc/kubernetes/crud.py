def delete(delete_func, name, delete_options, namespace="default", **kwargs):
    api_response = delete_func(name, namespace, body=delete_options, **kwargs).to_dict()
    return api_response
