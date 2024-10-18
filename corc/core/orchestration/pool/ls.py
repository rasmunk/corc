import os
from corc.core.orchestration.pool.models import discover_pools


async def ls(*args, **kwargs):
    response = {}
    # TODO, switch to using the kwargs path
    # path = kwargs.get("path", os.getcwd())
    pools = await discover_pools(os.getcwd())
    if not pools:
        response["pools"] = []
        response["msg"] = "No pools found."
        return True, response

    response["pools"] = pools
    response["msg"] = "Found pools."
    return True, response
