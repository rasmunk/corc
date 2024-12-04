from corc.core.defaults import SWARM
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.swarm.defaults import default_swarm_perstistence_path


async def get_member_state(member):
    # TODO, get the state of the member
    pass


async def sync(name, directory=None):
    if not directory:
        directory = default_swarm_perstistence_path
    response = {}

    swarm_db = DictDatabase(SWARM, directory=directory)
    if not await swarm_db.exists():
        response["msg"] = "Swarm {} does not exist.".format(name)
        return False, response

    swarm = await swarm_db.get(name)
    if not swarm:
        response["msg"] = "Swarm {} does not exist.".format(name)
        return False, response

    # TODO, get the state of all members

    return True, response
