from corc.core.storage.dictdatabase import DictDatabase
from corc.core.orchestration.stack.config import (
    get_stack_config,
    get_stack_config_instances,
    get_stack_config_pools,
)


async def update(*args, **kwargs):
    response = {}
    name = args[0]
    config_file = kwargs.get("config_file", None)
    directory = kwargs.get("directory", None)

    stack_db = DictDatabase(name, directory=directory)
    if not await stack_db.exists():
        response["msg"] = (
            "The Stack: {} database does not exist in directory: {}.".format(
                name, directory
            )
        )
        return False, response

    stack_to_update = await stack_db.get(name)
    if not stack_to_update:
        response["msg"] = (
            "Failed to find a Stack inside the database with name: {} to update.".format(
                name
            )
        )
        return False, response

    # Load the architecture file and deploy the stack
    stack_config = await get_stack_config(config_file)
    if not stack_config:
        response["msg"] = "Failed to load the Stack configuration file: {}.".format(
            config_file
        )
        return False, response

    # Extract the pool configurations
    stack_to_update["config"]["pools"] = await get_stack_config_pools(stack_config)

    # Extract the instance configurations
    instances_success, instances_response = await get_stack_config_instances(
        stack_config
    )
    if not instances_success:
        return False, instances_response
    stack_to_update["config"]["instances"] = instances_response

    if not await stack_db.update(name, stack_to_update):
        response["msg"] = (
            "Failed to save the updated Stack information to the database: {}".format(
                stack_db.name
            )
        )
        return False, response

    response["msg"] = "The Stack: {} has been updated.".format(name)
    return True, response
