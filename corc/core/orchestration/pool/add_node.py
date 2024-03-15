from corc.core.pool.models import Pool, Node


async def add_node(pool_name, *node_args, **node_kwargs):
    response = {}
    pool = Pool(pool_name)
    if not await pool.exists():
        response["msg"] = f"Pool does not exist: {pool.name}"
        return False, response

    if await pool.get(node_args[0]):
        response["msg"] = "Node already exists in pool."
        return False, response

    added = await pool.add(Node(*node_args))
    if not added:
        response["msg"] = "Failed to add node to pool."
        return False, response

    response["msg"] = "Added node to pool."
    return True, response
