from corc.core.storage.dictdatabase import DictDatabase


async def create(*args, **kwargs):
    response = {}

    stack = DictDatabase(*args, **kwargs)
    if await stack.exists():
        response["stack"] = stack
        response["msg"] = "Stack already exists."
        return True, response

    created = await stack.touch()
    if not created:
        response["msg"] = "Failed to create Stack."
        return False, response

    response["stack"] = stack
    response["msg"] = "Created Stack succesfully."
    return True, response
