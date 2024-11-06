from corc.core.storage.dictdatabase import DictDatabase


async def remove(name, directory=None):
    response = {}

    stack = DictDatabase(name, directory=directory)
    if not await stack.exists():
        response["msg"] = f"Stack does already not exist: {stack.name}."
        return True, response

    if not await stack.remove_persistence():
        response["msg"] = f"Failed to remove stack: {stack.name}."
        return False, response

    response["msg"] = f"Removed stack: {stack.name}."
    return True, response
