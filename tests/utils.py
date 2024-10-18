import concurrent


def execute_func_in_future(func, *action_args, **action_kwargs):
    """
    Execute a function in a separate thread and return the result.
    This is particularly useful when executing a function that
    spawns its own event loop.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *action_args, **action_kwargs)
        return future.result()
