from corc.core.defaults import SWARM
from corc.core.config import load_config
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.swarm.defaults import default_swarm_perstistence_path


async def create(name, config_file=None, directory=None):
    if not directory:
        directory = default_swarm_perstistence_path
    response = {}

    swarm_db = DictDatabase(SWARM, directory=directory)
    if not await swarm_db.exists():
        if not await swarm_db.touch():
            response["msg"] = (
                "The Swarm database: {} did not exist in directory: {}, and it could not be created.".format(
                    swarm_db.name, directory
                )
            )
            return False, response

    if await swarm_db.get(name):
        response["msg"] = (
            "The Swarm: {} already exists and therefore can't be created.".format(name)
        )
        return False, response

    swarm = {"id": name, "members": {}}
    # Load the swarm configuration file
    if config_file:
        swarm_config = load_config(path=config_file)
        if not swarm_config:
            response["msg"] = "Failed to load the Swarm configuration file: {}.".format(
                config_file
            )
            return False, response

        swarm["members"] = swarm_config.get("members", {})

    if not await swarm_db.add(swarm):
        response["msg"] = "Failed to save the Swarm: {} to the database: {}".format(
            name, swarm_db.name
        )
        return False, response

    response["swarm"] = swarm
    response["msg"] = "Created Swarm succesfully."
    return True, response
