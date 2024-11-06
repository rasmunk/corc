from corc.core.defaults import default_persistence_path, SWARM
from corc.core.storage.dictdatabase import discover_databases, DictDatabase, get_database_possible_postfixes


async def ls(*args, directory=None):
    if not directory:
        directory = default_persistence_path
    response = {}

    swarm_db_path = await discover_databases(directory, database_prefix=SWARM)
    if not swarm_db_path:
        response["swarms"] = []
        response["msg"] = "No Swarm Database was found in directory: {}.".format(directory)
        return True, response

    swarm_db = DictDatabase(SWARM, directory=directory)
    if not await swarm_db.exists():
        response["swarms"] = []
        response["msg"] = "No Swarm Database was found in: {}.".format(swarm_db.get_database_path())
        return True, response

    response["swarms"] = await swarm_db.items()
    response["msg"] = "Found swarms."
    return True, response
