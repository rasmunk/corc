import os
from corc.core.orchestration.pool.models import discover_pools


async def ls(*args, **kwargs):
    response = {}
    directory = kwargs.get("directory", os.getcwd())
    pools = await discover_pools(directory)
    if not pools:
        response["pools"] = []
        response["msg"] = "No pools found."
        return True, response

    response["pools"] = pools
    response["msg"] = "Found pools."
    return True, response
