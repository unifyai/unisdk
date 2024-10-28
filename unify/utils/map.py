import asyncio
import threading
from typing import Any, List


# noinspection PyShadowingBuiltins
def map(fn: callable, *args, mode="threading", **kwargs) -> Any:

    assert mode in (
        "threading",
        "asyncio",
    ), "map mode must be one of threading or asyncio."

    if args:
        num_calls = len(args[0])
    else:
        for v in kwargs.values():
            if isinstance(v, list):
                num_calls = len(v)
                break
        else:
            raise Exception(
                "At least one of the args or kwargs must be a list, "
                "which is to be mapped across the threads",
            )

    if mode == "threading":

        def fn_w_indexing(rets: List[None], thread_idx: int, *a, **kw):
            ret = fn(*a, **kw)
            rets[thread_idx] = ret

        threads = list()
        returns = [None] * num_calls
        for i in range(num_calls):
            a = tuple(a[i] for a in args)
            kw = {k: v[i] if isinstance(v, list) else v for k, v in kwargs.items()}
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

    fns = []
    for i in range(num_calls):
        a = (a[i] for a in args)
        kw = {k: v[i] for k, v in kwargs.items()}
        fns.append(fn(*a, **kw))

    async def main():
        return await asyncio.gather(*fns)

    return asyncio.run(main())
