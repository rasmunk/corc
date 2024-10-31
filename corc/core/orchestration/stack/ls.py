from corc.core.defaults import default_persistence_path
from corc.core.storage.dictdatabase import discover_databases


async def ls(*args, **kwargs):
    response = {}
    directory = kwargs.get("directory", default_persistence_path)
    stacks = await discover_databases(directory)
    if not stacks:
        response["stacks"] = []
        response["msg"] = "No stacks found."
        return True, response

    response["stacks"] = stacks
    response["msg"] = "Found stacks."
    return True, response
