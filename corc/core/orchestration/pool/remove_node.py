from corc.core.pool.models import Pool, Node


async def remove_node(pool_name, node_id):
    response = {}
    pool = Pool(pool_name)
    if not await pool.exists():
        response["msg"] = f"Pool does not exist: {pool.name}"
        return False, response

    if not await pool.remove(node_id):
        response["msg"] = "Failed to remove node from pool."

    response["msg"] = "Removed node from pool."
    return True, response
