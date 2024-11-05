from corc.core.defaults import default_persistence_path
from corc.core.storage.dictdatabase import discover_databases


async def ls(*args, directory=None):
    if not directory:
        directory = default_persistence_path
    response = {}

    swarms = await discover_databases(directory)
    if not swarms:
        response["swarms"] = []
        response["msg"] = "No swarms found."
        return True, response

    response["swarms"] = swarms
    response["msg"] = "Found swarms."
    return True, response
