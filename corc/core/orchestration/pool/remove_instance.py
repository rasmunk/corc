from corc.core.orchestration.pool.models import Pool


async def remove_instance(pool_name, node_id):
    response = {}
    pool = Pool(pool_name)
    if not await pool.exists():
        response["msg"] = f"Pool does not exist: {pool.name}"
        return False, response

    if not await pool.remove(node_id):
        response["msg"] = "Failed to remove node from pool."

    response["msg"] = "Removed node from pool."
    return True, response
