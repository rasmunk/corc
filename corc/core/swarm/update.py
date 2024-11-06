from corc.core.defaults import SWARM
from corc.core.swarm.defaults import default_swarm_perstistence_path
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.config import load_config


async def update(name, config_file=None, directory=None):
    if not directory:
        directory = default_swarm_perstistence_path
    response = {}

    swarm_db = DictDatabase(SWARM, directory=directory)
    if not await swarm_db.exists():
        response["msg"] = (
            "The Swarm: {} database does not exist in directory: {}.".format(
                SWARM, directory
            )
        )
        return False, response

    swarm_to_update = await swarm_db.get(name)
    if not swarm_to_update:
        response["msg"] = (
            "Failed to find a Swarm inside the database with name: {} to update.".format(
                name
            )
        )
        return False, response

    # Load the config file
    swarm_config = load_config(path=config_file)
    if not swarm_config:
        response["msg"] = "Failed to load the Swarm configuration file: {}.".format(
            config_file
        )
        return False, response

    swarm_to_update["members"] = swarm_config.get("members", {})
    if not await swarm_db.update(name, swarm_to_update):
        response["msg"] = (
            "Failed to save the updated Swarm information to the database: {}".format(
                swarm_db.name
            )
        )
        return False, response

    response["msg"] = "The Swarm: {} has been updated.".format(name)
    return True, response
