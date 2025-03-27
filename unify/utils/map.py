import asyncio
import contextvars
import threading
from typing import Any, List

from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio

MAP_MODE = "threading"


def set_map_mode(mode: str):
    global MAP_MODE
    MAP_MODE = mode


def get_map_mode() -> str:
    return MAP_MODE


def _is_iterable(item: Any) -> bool:
    try:
        iter(item)
        return True
    except TypeError:
        return False


# noinspection PyShadowingBuiltins
def map(
    fn: callable,
    *args,
    mode=None,
    name="",
    from_args=False,
    raise_exceptions=True,
    **kwargs,
) -> Any:

    if name:
        name = (
            " ".join(substr[0].upper() + substr[1:] for substr in name.split("_")) + " "
        )

    if mode is None:
        mode = get_map_mode()

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
        args_n_kwargs = args[0]
        if not isinstance(args_n_kwargs[0], tuple):
            if isinstance(args_n_kwargs[0], dict):
                args_n_kwargs = [((), item) for item in args_n_kwargs]
            else:
                args_n_kwargs = [((item,), {}) for item in args_n_kwargs]
        elif (
            not isinstance(args_n_kwargs[0][0], tuple)
            or len(args_n_kwargs[0]) < 2
            or not isinstance(args_n_kwargs[0][1], dict)
        ):
            args_n_kwargs = [(item, {}) for item in args_n_kwargs]
        num_calls = len(args_n_kwargs)

    if mode == "loop":

        pbar = tqdm(total=num_calls)
        pbar.set_description(f"{name}Iterations")

        returns = list()
        for a, kw in args_n_kwargs:
            ret = fn_w_exception_handling(*a, **kw)
            returns.append(ret)
            pbar.update(1)
        pbar.close()
        return returns

    elif mode == "threading":

        pbar = tqdm(total=num_calls)
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
            return await tqdm_asyncio.gather(*fns, desc=f"{name}Coroutines")

        ret += asyncio.run(main(fns))

    ret = []
    thread = threading.Thread(target=_run_asyncio_in_thread, args=(ret,))
    thread.start()
    thread.join()
    return ret
