from corc.core.orchestration.pool.models import Pool, Instance


async def add_instance(pool_name, instance_name, **kwargs):
    response = {}

    pool_directory = kwargs.pop("directory", None)
    pool = Pool(pool_name, directory=pool_directory)
    if not await pool.exists():
        response["msg"] = f"Pool does not exist: {pool.name}"
        return False, response

    if await pool.get(instance_name):
        response["msg"] = "Instance already exists in pool."
        return False, response

    added = await pool.add(Instance(instance_name, **kwargs))
    if not added:
        response["msg"] = "Failed to add instance to pool."
        return False, response

    response["msg"] = "Added instance to pool."
    return True, response
