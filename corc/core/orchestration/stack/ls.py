from corc.core.defaults import STACK
from corc.core.storage.dictdatabase import DictDatabase


async def ls(*args, **kwargs):
    response = {}
    stack_db = DictDatabase(STACK)
    stacks = await stack_db.items()
    if not stacks:
        response["msg"] = "No stacks found."
        return False, response

    response["stacks"] = stacks
    response["msg"] = "Found stacks."
    return True, response
