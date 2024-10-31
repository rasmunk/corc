from corc.core.storage.dictdatabase import DictDatabase
from corc.core.orchestration.stack.config import (
    get_stack_config,
    get_stack_config_instances,
)


async def create(*args, **kwargs):
    response = {}

    stack_db = DictDatabase(*args, **kwargs)
    if await stack_db.exists():
        response["msg"] = "The Stack: {} database already exists.".format(stack_db.name)
        return True, response

    created = await stack.touch()
    if not created:
        response["msg"] = "Failed to create the Stack database."
        return False, response

    # TODO, also allow this to happend via an update call
    stack = {"id": name, "config": {}, "instances": {}, "pools": {}}

    # Load the architecture file and deploy the stack
    stack_config = await get_stack_config(deploy_file)
    if not stack_config:
        return False, {"error": "Failed to load stack config."}
    stack["config"] = stack_config

    success, response = await get_stack_config_instances(stack_config)
    if not success:
        return False, response
    instances = response
    stack["config"]["instances"] = instances

    for pool_name, pool_kwargs in stack_config.get("pools", {}).items():
        pool = Pool(pool_name)
        stack["pools"][pool_name] = pool
        for instance_name in pool_kwargs.get("instances", []):
            if instance_name in stack["instances"]:
                added = await pool.add(stack["instances"][instance_name])
                if not added:
                    print(
                        "Failed to add instance: {} to pool: {}.".format(
                            instance_name, pool_name
                        )
                    )
                else:
                    print(
                        "Added instance: {} to pool: {}.".format(
                            instance_name, pool_name
                        )
                    )
    if not await stack_db.add(stack):
        return False, {
            "error": "Failed to save the Stack information to the database: {}".format(
                stack_db.name
            )
        }

    response["stack"] = stack
    response["msg"] = "Created Stack succesfully."
    return True, response
