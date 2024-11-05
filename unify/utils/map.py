import asyncio
import threading
import contextvars
from tqdm import tqdm
from typing import Any, List


def _is_iterable(item: Any) -> bool:
    try:
        iter(item)
        return True
    except TypeError:
        return False


# noinspection PyShadowingBuiltins
def map(fn: callable, *args, mode="threading", **kwargs) -> Any:

    assert mode in (
        "threading",
        "asyncio",
    ), "map mode must be one of threading or asyncio."

    args = list(args)
    for i, a in enumerate(args):
        if _is_iterable(a):
            args[i] = list(a)

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

    pbar = tqdm(total=num_calls)

    if mode == "threading":

        pbar.set_description("Threads Completed")

        def fn_w_indexing(rets: List[None], thread_idx: int, *a, **kw):
            for var, value in kw["context"].items():
                var.set(value)
            del kw["context"]
            ret = fn(*a, **kw)
            pbar.update(1)
            rets[thread_idx] = ret

        threads = list()
        returns = [None] * num_calls
        for i in range(num_calls):
            a = tuple(a[i] for a in args)
            kw = {
                k: v[i] if (isinstance(v, list) or isinstance(v, tuple)) else v
                for k, v in kwargs.items()
            }
            kw["context"] = contextvars.copy_context()
            thread = threading.Thread(
                target=fn_w_indexing,
                args=(returns, i, *a),
                kwargs=kw,
            )
            thread.start()
            threads.append(thread)
        [thread.join() for thread in threads]
        pbar.close()
        return returns

    pbar.set_description("Coroutines Completed")

    async def _wrapped(*a, **kw):
        ret = await fn(*a, **kw)
        pbar.update(1)
        return ret

    fns = []
    for i in range(num_calls):
        a = (a[i] for a in args)
        kw = {
            k: v[i] if (isinstance(v, list) or isinstance(v, tuple)) else v
            for k, v in kwargs.items()
        }
        fns.append(_wrapped(*a, **kw))

    async def main():
        ret = await asyncio.gather(*fns)
        pbar.close()
        return ret

    return asyncio.run(main())
