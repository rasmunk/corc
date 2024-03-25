from corc.core.defaults import STACK
from corc.core.storage.dictdatabase import DictDatabase


async def show(*args, **kwargs):
    response = {}
    name = args[0]
    stack_db = DictDatabase(STACK)
    stack = await stack_db.get(name)
    if not stack:
        response["msg"] = f"Stack does not exist: {name}."
        return False, response

    response["stack"] = stack
    response["msg"] = "Stack details."
    return True, response
