from corc.core.storage.dictdatabase import DictDatabase
from corc.core.defaults import SWARM


async def show(name, directory=None):
    response = {}

    swarm = DictDatabase(SWARM, directory=directory)
    if not await swarm.exists():
        response["msg"] = "Swarm {} does not exist.".format(swarm.name)
        return False, response

    response["swarm"] = await swarm.items()
    response["msg"] = "Swarm details."
    return True, response
