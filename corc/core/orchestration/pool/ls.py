from corc.core.defaults import default_persistence_path
from corc.core.storage.dictdatabase import discover_databases


async def ls(*args, **kwargs):
    response = {}
    directory = kwargs.get("directory", default_persistence_path)
    pools = await discover_databases(directory)
    if not pools:
        response["pools"] = []
        response["msg"] = "No pools found."
        return True, response

    response["pools"] = pools
    response["msg"] = "Found pools."
    return True, response
