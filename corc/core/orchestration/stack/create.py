from corc.core.storage.dictdatabase import DictDatabase
from corc.core.orchestration.stack.config import (
    get_stack_config,
    get_stack_config_instances,
    get_stack_config_pools,
)


async def create(*args, **kwargs):
    response = {}
    name = args[0]
    definition_file = kwargs.get("definition_file", None)
    directory = kwargs.get("directory", None)

    stack_db = DictDatabase(name, directory=directory)
    if not await stack_db.exists():
        if not await stack_db.touch():
            response["msg"] = (
                "The Stack database: {} did not exist in directory: {}, and it could not be created.".format(
                    stack_db.name, directory
                )
            )
            return False, response

    stack = {"id": name, "config": {}, "instances": {}, "pools": {}}

    # Load the stack configuration file
    stack_config = await get_stack_config(definition_file)
    if not stack_config:
        return False, {"error": "Failed to load stack config."}

    # Extract the pool configurations
    stack["config"]["pools"] = await get_stack_config_pools(stack_config)

    # Extract the instance configurations
    instances_success, instances_response = await get_stack_config_instances(
        stack_config
    )
    if not instances_success:
        return False, instances_response
    stack["config"]["instances"] = instances_response

    if not await stack_db.add(stack):
        return False, {
            "error": "Failed to save the Stack information to the database: {}".format(
                stack_db.name
            )
        }

    response["stack"] = stack
    response["msg"] = "Created Stack succesfully."
    return True, response
