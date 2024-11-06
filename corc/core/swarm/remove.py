from corc.core.swarm.defaults import default_swarm_perstistence_path
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.defaults import SWARM


async def remove(name, directory=None):
    if not directory:
        directory = default_swarm_perstistence_path
    response = {}

    swarm_db = DictDatabase(SWARM, directory=directory)
    if not await swarm_db.exists():
        response["msg"] = "The Swarm Database: {} already does not exist.".format(
            swarm_db.name
        )
        return True, response

    if not await swarm_db.get(name):
        response["msg"] = "The Swarm: {} does not exist.".format(name)
        return True, response

    if not await swarm_db.remove(name):
        response["msg"] = "Failed to remove swarm: {}.".format(name)
        return False, response

    response["msg"] = "Removed swarm: {}.".format(name)
    return True, response
