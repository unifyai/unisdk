import asyncio
import contextvars
import os
import threading
from typing import Any, Callable, List

from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio

_DEFAULT_MAP_MODE = "threading"


def _is_iterable(item: Any) -> bool:
    try:
        iter(item)
        return True
    except TypeError:
        return False


# noinspection PyShadowingBuiltins
def map(
    fn: Callable,
    *args,
    mode: str = None,
    name: str = "",
    from_args: bool = False,
    raise_exceptions: bool = True,
    **kwargs,
) -> List[Any]:
    """
    Apply a function to items in parallel using threads, asyncio, or a sequential loop.

    There are two primary usage patterns controlled by the `from_args` parameter:

    **Pattern 1: from_args=False (default) - Map over a list of items**

    Pass a single list of items as the first positional argument. Each item becomes
    the first positional argument to `fn`. Additional kwargs are forwarded to every
    call.

    Examples::

        # Simple: each item passed as first arg
        unify.map(process, [item1, item2, item3])
        # Calls: process(item1), process(item2), process(item3)

        # With kwargs: kwargs forwarded to all calls
        unify.map(embed, ["text1", "text2"], model="gpt-4", dimensions=512)
        # Calls: embed("text1", model="gpt-4", dimensions=512),
        #        embed("text2", model="gpt-4", dimensions=512)

        # Explicit (args, kwargs) tuples for per-item control
        unify.map(fn, [
            (("arg1",), {"k": 1}),
            (("arg2",), {"k": 2}),
        ])
        # Calls: fn("arg1", k=1), fn("arg2", k=2)

    **Pattern 2: from_args=True - Parallel iteration over multiple sequences**

    Pass multiple positional args and/or kwargs as lists. Lists are zipped together
    and iterated in parallel. Scalar kwargs are broadcast to all calls.

    Examples::

        # Positional args as parallel lists
        unify.map(add, [1, 2, 3], [4, 5, 6], from_args=True)
        # Calls: add(1, 4), add(2, 5), add(3, 6)

        # Kwargs as parallel lists
        unify.map(log, project="myproject", a=[1, 2], b=[3, 4], from_args=True)
        # Calls: log(project="myproject", a=1, b=3),
        #        log(project="myproject", a=2, b=4)

        # Mixed: scalar kwargs broadcast, list kwargs vary per call
        unify.map(fn, x=[1, 2, 3], constant="same", from_args=True)
        # Calls: fn(x=1, constant="same"), fn(x=2, constant="same"), ...

    Args:
        fn: The function to apply to each item.
        *args: When from_args=False, a single list of items to map over.
               When from_args=True, multiple sequences to zip and iterate.
        mode: Execution mode - "threading" (default), "asyncio", or "loop".
        name: Optional name for progress bar description.
        from_args: If False (default), map over items in first arg with kwargs
                   forwarded to all calls. If True, zip args/kwargs as parallel
                   sequences.
        raise_exceptions: If True (default), re-raise exceptions from fn.
                          If False, exceptions are silently caught and None returned.
        **kwargs: When from_args=False, forwarded to every call of fn.
                  When from_args=True, list kwargs are indexed per call,
                  scalar kwargs are broadcast to all calls.

    Returns:
        List of return values from each call to fn, in the same order as inputs.
    """

    if name:
        name = (
            " ".join(substr[0].upper() + substr[1:] for substr in name.split("_")) + " "
        )

    if mode is None:
        mode = _DEFAULT_MAP_MODE

    assert mode in (
        "threading",
        "asyncio",
        "loop",
    ), "map mode must be one of threading, asyncio or loop."

    def fn_w_exception_handling(*a, **kw):
        try:
            return fn(*a, **kw)
        except Exception as e:
            if raise_exceptions:
                raise e

    if from_args:
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
        args_n_kwargs = [
            (
                tuple(a[i] for a in args),
                {
                    k: v[i] if (isinstance(v, list) or isinstance(v, tuple)) else v
                    for k, v in kwargs.items()
                },
            )
            for i in range(num_calls)
        ]
    else:
        items = args[0]
        if not isinstance(items[0], tuple):
            if isinstance(items[0], dict):
                # Items are dicts - merge with kwargs
                args_n_kwargs = [((), {**item, **kwargs}) for item in items]
            else:
                # Items are scalars - pass as first arg, forward kwargs
                args_n_kwargs = [((item,), kwargs.copy()) for item in items]
        elif (
            not isinstance(items[0][0], tuple)
            or len(items[0]) < 2
            or not isinstance(items[0][1], dict)
        ):
            # Items are tuples but not (args, kwargs) format - pass as args, forward kwargs
            args_n_kwargs = [(item, kwargs.copy()) for item in items]
        else:
            # Items are already (args, kwargs) tuples - merge kwargs
            args_n_kwargs = [(a, {**kw, **kwargs}) for a, kw in items]
        num_calls = len(args_n_kwargs)

    if mode == "loop":

        pbar = tqdm(total=num_calls, disable=os.environ.get("TQDM_DISABLE", "0") == "1")
        pbar.set_description(f"{name}Iterations")

        returns = list()
        for a, kw in args_n_kwargs:
            ret = fn_w_exception_handling(*a, **kw)
            returns.append(ret)
            pbar.update(1)
        pbar.close()
        return returns

    elif mode == "threading":

        pbar = tqdm(total=num_calls, disable=os.environ.get("TQDM_DISABLE", "0") == "1")
        pbar.set_description(f"{name}Threads")

        def fn_w_indexing(rets: List[None], thread_idx: int, *a, **kw):
            for var, value in kw["context"].items():
                var.set(value)
            del kw["context"]
            ret = fn_w_exception_handling(*a, **kw)
            pbar.update(1)
            rets[thread_idx] = ret

        threads = list()
        returns = [None] * num_calls
        for i, a_n_kw in enumerate(args_n_kwargs):
            a, kw = a_n_kw
            kw = kw.copy()  # Avoid mutating the original dict
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

    def _run_asyncio_in_thread(ret):
        asyncio.set_event_loop(asyncio.new_event_loop())
        MAX_WORKERS = 100
        semaphore = asyncio.Semaphore(MAX_WORKERS)
        fns = []

        async def fn_wrapper(*args, **kwargs):
            async with semaphore:
                return await asyncio.to_thread(fn_w_exception_handling, *args, **kwargs)

        for _, a_n_kw in enumerate(args_n_kwargs):
            a, kw = a_n_kw
            fns.append(fn_wrapper(*a, **kw))

        async def main(fns):
            return await tqdm_asyncio.gather(
                *fns,
                desc=f"{name}Coroutines",
                disable=os.environ.get("TQDM_DISABLE", "0") == "1",
            )

        ret += asyncio.run(main(fns))

    ret = []
    thread = threading.Thread(target=_run_asyncio_in_thread, args=(ret,))
    thread.start()
    thread.join()
    return ret
