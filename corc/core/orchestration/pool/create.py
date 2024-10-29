from corc.core.orchestration.pool.models import Pool


async def create(*args, **kwargs):
    response = {}
    pool = Pool(*args, **kwargs)
    if await pool.exists():
        response["pool"] = pool
        response["msg"] = "Pool already exists."
        return True, response

    created = await pool.touch()
    if not created:
        response["msg"] = "Failed to create pool."
        return False, response

    response["pool"] = pool
    response["msg"] = "Created pool successfully."
    return True, response
