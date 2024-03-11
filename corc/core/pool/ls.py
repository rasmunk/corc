import os
from corc.core.pool.models import discover_pools


async def ls(*args, **kwargs):
    response = {}
    # Note, simple discover method that has be to be improved.
    # Might create a designed path where the pools are stored
    pools = await discover_pools(os.getcwd())
    if not pools:
        response["msg"] = "No pools found."
        return True, response

    response["pools"] = pools
    response["msg"] = "pools"
    return True, response
