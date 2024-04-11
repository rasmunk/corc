from corc.core.orchestration.pool.models import Pool


async def remove(*args, **kwargs):
    response = {}
    pool = Pool(*args)
    exists = await pool.exists()
    if not exists:
        response["msg"] = f"Pool does already not exist: {pool.name}."
        return True, response

    removed = await pool.remove_persistence()
    if not removed:
        response["msg"] = f"Failed to remove pool: {pool.name}."
        return False, response

    response["msg"] = f"Removed pool: {pool.name}."
    return True, response
