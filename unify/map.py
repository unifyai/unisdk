import asyncio
import threading
from typing import Any, List, Iterable
import copy


# noinspection PyShadowingBuiltins
def map(fn: callable, args=None, kwargs=None, mode="threading") -> Any:
    assert mode in (
        "threading",
        "asyncio",
    ), "map mode must be one of threading or asyncio."

    args = args if args is not None else []
    kwargs = kwargs if kwargs is not None else {}

    # these conditions could be refactored to be written in a much cleaner way
    if not isinstance(args, (list, tuple)) and not isinstance(kwargs, (list, tuple)):
        args = [args]
        kwargs = [kwargs]
        num_calls = 1
    elif not isinstance(args, (list, tuple)) and isinstance(kwargs, (list, tuple)):
        args = [copy.deepcopy(args) for _ in kwargs]
        num_calls = len(kwargs)
    elif not isinstance(kwargs, (list, tuple)) and isinstance(args, (list, tuple)):
        kwargs = [copy.deepcopy(kwargs) for _ in args]
        num_calls = len(args)
    else:
        if len(args) != len(kwargs):
            raise Exception(
                "if both args and kwargs are iterable, they must be of the same length."
            )
        num_calls = len(args)

    if mode == "threading":

        def fn_w_indexing(rets: List[None], thread_idx: int, *a, **kw):
            ret = fn(*a, **kw)
            rets[thread_idx] = ret

        threads = list()
        returns = [None] * num_calls
        for i in range(num_calls):
            curr_args = (
                args[i]
                if isinstance(args[i], (list, tuple))
                else (args[i],) if args else ()
            )
            curr_kwargs = kwargs[i] if kwargs else {}
            thread = threading.Thread(
                target=fn_w_indexing,
                args=(returns, i, *curr_args),
                kwargs=curr_kwargs,
            )
            thread.start()
            threads.append(thread)
        [thread.join() for thread in threads]
        return returns

    # noinspection PyShadowingNames

    # this wont work in jupyter environments atm
    fns = []
    for i in range(num_calls):
        curr_args = (
            args[i]
            if isinstance(args[i], (list, tuple))
            else (args[i],) if args else ()
        )
        curr_kwargs = kwargs[i] if kwargs else {}
        fns.append(fn(*curr_args, **curr_kwargs))

    async def main():
        return await asyncio.gather(*fns)

    return asyncio.run(main())
