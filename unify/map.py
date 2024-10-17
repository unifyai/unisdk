import asyncio
import threading
from typing import Any, List


# noinspection PyShadowingBuiltins
def map(fn: callable, *args, mode="threading", **kwargs) -> Any:

    assert mode in (
        "threading",
        "asyncio",
    ), "map mode must be one of threading or asyncio."

    num_calls = len(args[0])

    if mode == "threading":

        def fn_w_indexing(rets: List[None], thread_idx: int, *a, **kw):
            ret = fn(*a, **kw)
            rets[thread_idx] = ret

        threads = list()
        returns = [None] * num_calls
        for i in range(num_calls):
            a = (a[i] for a in args)
            kw = {k: v[i] for k, v in kwargs.items()}
            thread = threading.Thread(
                target=fn_w_indexing,
                args=(returns, i, *a),
                kwargs=kw,
            )
            thread.start()
            threads.append(thread)
        [thread.join() for thread in threads]
        return returns

    # noinspection PyShadowingNames
    async def async_fn():
        rets = list()
        for i in range(num_calls):
            a = (a[i] for a in args)
            kw = {k: v[i] for k, v in kwargs.items()}
            rets.append(await fn(*a, **kw))
        return rets

    return asyncio.run(async_fn())
