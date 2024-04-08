from kubernetes import client


def request(func, *args, catch=False, **kwargs):
    if catch:
        try:
            return True, func(*args, **kwargs)
        except client.rest.ApiException as err:
            return False, err
    else:
        return True, func(*args, **kwargs)
