from corc.core.pool.models import Pool


async def show(*args, **kwargs):
    response = {}
    pool = Pool(*args)
    if not await pool.exists():
        response["msg"] = f"Pool does not exist: {pool.name}"
        return False, response

    response["members"] = await pool.items()
    response["msg"] = "Pool members."
    return True, response
