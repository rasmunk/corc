from corc.core.storage.dictdatabase import DictDatabase


async def remove(*args, **kwargs):
    response = {}
    stack = DictDatabase(*args, **kwargs)
    exists = await stack.exists()
    if not exists:
        response["msg"] = f"Stack does already not exist: {stack.name}."
        return True, response

    removed = await stack.remove_persistence()
    if not removed:
        response["msg"] = f"Failed to remove stack: {stack.name}."
        return False, response

    response["msg"] = f"Removed stack: {stack.name}."
    return True, response
