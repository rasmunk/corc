from corc.core.storage.dictdatabase import DictDatabase


async def show(*args, **kwargs):
    response = {}

    stack = DictDatabase(*args, **kwargs)
    if not await stack.exists():
        response["msg"] = "Stack {} does not exist.".format(stack.name)
        return False, response

    response["stack"] = await stack.items()
    response["msg"] = "Stack details."
    return True, response
