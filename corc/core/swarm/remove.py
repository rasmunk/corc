from corc.core.storage.dictdatabase import DictDatabase
from corc.core.defaults import SWARM


async def remove(name, directory=None):
    response = {}

    swarm = DictDatabase(SWARM, directory=directory)
    if not await swarm.exists():
        response["msg"] = "The Swarm Database: {} already does not exist.".format(
            swarm.name
        )
        return True, response

    if not await swarm.remove_persistence():
        response["msg"] = "Failed to remove swarm: {}.".format(swarm.name)
        return False, response

    response["msg"] = "Removed swarm: {}.".format(swarm.name)
    return True, response
