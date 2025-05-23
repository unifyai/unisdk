import asyncio
import json
import os
import time
import traceback

import pytest
import unify
from tests.test_logging.helpers import _handle_project
from tests.test_utils.helpers import _CacheHandler
from unify import AsyncUnify, Unify
from unify.utils._caching import UPSTREAM_CACHE_CONTEXT_NAME


# noinspection PyBroadException
def test_cache() -> None:
    with _CacheHandler() as cache_handler:
        client = Unify(
            endpoint="gpt-4o@openai",
        )
        t = time.perf_counter()
        r0 = client.generate(user_message="hello", cache=True)
        t0 = time.perf_counter() - t
        assert os.path.exists(cache_handler.test_path)
        mt0 = os.path.getmtime(cache_handler.test_path)
        t = time.perf_counter()
        r1 = client.generate(user_message="hello", cache=True)
        mt1 = os.path.getmtime(cache_handler.test_path)
        t1 = time.perf_counter() - t
        assert t1 < t0
        assert mt0 == mt1
        assert r0 == r1


@pytest.mark.asyncio
async def test_cache_async():
    with _CacheHandler() as cache_handler:
        client = AsyncUnify(
            endpoint="gpt-4o@openai",
            cache=True,
        )

        t = time.perf_counter()
        r0 = await client.generate(user_message="hello")
        t0 = time.perf_counter() - t
        mt0 = os.path.getmtime(cache_handler.test_path)

        t = time.perf_counter()
        r1 = await client.generate(user_message="hello")
        mt1 = os.path.getmtime(cache_handler.test_path)
        t1 = time.perf_counter() - t

        await client.close()
        assert os.path.exists(cache_handler.test_path)
        assert t1 < t0
        assert mt0 == mt1
        assert r0 == r1


# noinspection PyBroadException
def test_cache_write() -> None:
    with _CacheHandler() as cache_handler:
        client = Unify(
            endpoint="gpt-4o@openai",
        )
        client.generate(user_message="hello", cache="write")
        assert os.path.exists(cache_handler.test_path)
        mt0 = os.path.getmtime(cache_handler.test_path)
        client.generate(user_message="hello", cache="write")
        mt1 = os.path.getmtime(cache_handler.test_path)
        assert mt0 < mt1


@pytest.mark.asyncio
async def test_cache_write_async() -> None:
    with _CacheHandler() as cache_handler:
        client = AsyncUnify(
            endpoint="gpt-4o@openai",
        )
        await client.generate(user_message="hello", cache="write")
        assert os.path.exists(cache_handler.test_path)
        mt0 = os.path.getmtime(cache_handler.test_path)
        await client.generate(user_message="hello", cache="write")
        mt1 = os.path.getmtime(cache_handler.test_path)
        assert mt0 < mt1
        await client.close()


# noinspection PyBroadException
def test_cache_read() -> None:
    with _CacheHandler() as cache_handler:
        client = Unify(
            endpoint="gpt-4o@openai",
        )
        t = time.perf_counter()
        r0 = client.generate(user_message="hello", cache="write")
        t0 = time.perf_counter() - t
        assert os.path.exists(cache_handler.test_path)
        mt0 = os.path.getmtime(cache_handler.test_path)
        t = time.perf_counter()
        r1 = client.generate(user_message="hello", cache="read")
        mt1 = os.path.getmtime(cache_handler.test_path)
        t1 = time.perf_counter() - t
        assert t1 < t0
        assert mt0 == mt1
        assert r0 == r1


@pytest.mark.asyncio
async def test_cache_read_async() -> None:
    with _CacheHandler() as cache_handler:
        client = AsyncUnify(
            endpoint="gpt-4o@openai",
        )
        t = time.perf_counter()
        r0 = await client.generate(user_message="hello", cache="write")
        t0 = time.perf_counter() - t
        assert os.path.exists(cache_handler.test_path)
        mt0 = os.path.getmtime(cache_handler.test_path)
        t = time.perf_counter()
        r1 = await client.generate(user_message="hello", cache="read")
        mt1 = os.path.getmtime(cache_handler.test_path)
        t1 = time.perf_counter() - t
        assert t1 < t0
        assert mt0 == mt1
        assert r0 == r1
        await client.close()


# noinspection PyBroadException
def test_cache_read_only() -> None:
    with _CacheHandler() as cache_handler:
        client = Unify(
            endpoint="gpt-4o@openai",
        )
        t = time.perf_counter()
        r0 = client.generate(user_message="hello", cache="write")
        t0 = time.perf_counter() - t
        assert os.path.exists(cache_handler.test_path)
        mt0 = os.path.getmtime(cache_handler.test_path)
        t = time.perf_counter()
        r1 = client.generate(user_message="hello", cache="read-only")
        mt1 = os.path.getmtime(cache_handler.test_path)
        t1 = time.perf_counter() - t
        assert t1 < t0
        assert mt0 == mt1
        assert r0 == r1
        os.remove(cache_handler.test_path)
        unify._caching._cache = None
        try:
            client.generate(user_message="hello", cache="read-only")
            raised_exception = False
        except Exception:
            raised_exception = True
        assert raised_exception, "read-only mode should have raised exception"


@pytest.mark.asyncio
async def test_cache_read_only_async() -> None:
    with _CacheHandler() as cache_handler:
        client = AsyncUnify(
            endpoint="gpt-4o@openai",
        )
        t = time.perf_counter()
        r0 = await client.generate(user_message="hello", cache="write")
        t0 = time.perf_counter() - t
        assert os.path.exists(cache_handler.test_path)
        mt0 = os.path.getmtime(cache_handler.test_path)
        t = time.perf_counter()
        r1 = await client.generate(user_message="hello", cache="read-only")
        mt1 = os.path.getmtime(cache_handler.test_path)
        t1 = time.perf_counter() - t
        assert t1 < t0
        assert mt0 == mt1
        assert r0 == r1
        os.remove(cache_handler.test_path)
        unify._caching._cache = None
        try:
            await client.generate(user_message="hello", cache="read-only")
            raised_exception = False
        except Exception:
            raised_exception = True
        assert raised_exception, "read-only mode should have raised exception"
        await client.close()


@pytest.mark.parametrize("traced", [True, False])
def test_cache_closest_match_on_exception(traced):
    with _CacheHandler() as cache_handler:
        client = Unify(
            endpoint="gpt-4o@openai",
            traced=traced,
        )
        r0 = client.generate(user_message="hello", cache="write")
        assert os.path.exists(cache_handler.test_path)
        raised_exception = True
        try:
            client.generate(user_message="helloo", cache="read-only")
            raised_exception = False
        except Exception:
            assert (
                """Failed to get cache for function chat.completions.create with kwargs {\n    "model": "gpt-4o@openai",\n    "messages": [\n        {\n            "role": "user",\n            "content": "helloo"\n        }\n    ],\n    "temperature": 1.0,\n    "stream": false,\n    "extra_body": {\n        "signature": "python",\n        "use_custom_keys": false,\n        "tags": null,\n        "drop_params": true,\n        "region": null,\n        "log_query_body": true,\n        "log_response_body": true\n    }\n} from cache at None. \n\nCorresponding key\nchat.completions.create_{"model": "gpt-4o@openai", "messages": [{"role": "user", "content": "helloo"}], "temperature": 1.0, "stream": false, "extra_body": {"signature": "python", "use_custom_keys": false, "tags": null, "drop_params": true, "region": null, "log_query_body": true, "log_response_body": true}}\nwas not found in the cache.\n\nThe closest match is:\nchat.completions.create_{"model": "gpt-4o@openai", "messages": [{"role": "user", "content": "hello"}], "temperature": 1.0, "stream": false, "extra_body": {"signature": "python", "use_custom_keys": false, "tags": null, "drop_params": true, "region": null, "log_query_body": true, "log_response_body": true}}\n\nThe contracted diff is:\nchat...."hell[-o-]o"}],...rue}}\n\n\n\n"""
                in traceback.format_exc()
            )
        assert raised_exception, "Failed to raise Exception"


def test_cache_file_union() -> None:
    first_cache_fpath = ".first_cache.json"
    second_cache_fpath = ".second_cache.json"
    target_cache_fpath = ".target_cache.json"
    first_cache = {"a": 0, "b": 1, "c": 2}
    second_cache = {"a": 0, "c": 3, "d": 4}
    with open(first_cache_fpath, "w+") as file:
        json.dump(first_cache, file)
    with open(second_cache_fpath, "w+") as file:
        json.dump(second_cache, file)

    raised = False
    try:
        unify.cache_file_union(
            first_cache_fpath,
            second_cache_fpath,
            target_cache_fpath,
        )
    except:
        raised = True
    assert raised, "conflict failed to raise exception"

    unify.cache_file_union(
        first_cache_fpath,
        second_cache_fpath,
        target_cache_fpath,
        conflict_mode="first_overrides",
    )

    with open(target_cache_fpath, "r") as file:
        target_cache = json.load(file)

    assert target_cache == {"a": 0, "b": 1, "c": 2, "d": 4}

    unify.cache_file_union(
        first_cache_fpath,
        second_cache_fpath,
        target_cache_fpath,
        conflict_mode="second_overrides",
    )

    with open(target_cache_fpath, "r") as file:
        target_cache = json.load(file)

    assert target_cache == {"a": 0, "b": 1, "c": 3, "d": 4}

    os.remove(first_cache_fpath)
    os.remove(second_cache_fpath)
    os.remove(target_cache_fpath)


def test_cache_file_intersection() -> None:
    first_cache_fpath = ".first_cache.json"
    second_cache_fpath = ".second_cache.json"
    target_cache_fpath = ".target_cache.json"
    first_cache = {"a": 0, "b": 1, "c": 2}
    second_cache = {"a": 0, "c": 3, "d": 4}
    with open(first_cache_fpath, "w+") as file:
        json.dump(first_cache, file)
    with open(second_cache_fpath, "w+") as file:
        json.dump(second_cache, file)

    raised = False
    try:
        unify.cache_file_intersection(
            first_cache_fpath,
            second_cache_fpath,
            target_cache_fpath,
        )
    except:
        raised = True
    assert raised, "conflict failed to raise exception"

    unify.cache_file_intersection(
        first_cache_fpath,
        second_cache_fpath,
        target_cache_fpath,
        conflict_mode="first_overrides",
    )

    with open(target_cache_fpath, "r") as file:
        target_cache = json.load(file)

    assert target_cache == {"a": 0, "c": 2}

    unify.cache_file_intersection(
        first_cache_fpath,
        second_cache_fpath,
        target_cache_fpath,
        conflict_mode="second_overrides",
    )

    with open(target_cache_fpath, "r") as file:
        target_cache = json.load(file)

    assert target_cache == {"a": 0, "c": 3}

    os.remove(first_cache_fpath)
    os.remove(second_cache_fpath)
    os.remove(target_cache_fpath)


def test_subtract_cache_files():
    first_cache_fpath = ".first_cache.json"
    second_cache_fpath = ".second_cache.json"
    target_cache_fpath = ".target_cache.json"
    first_cache = {"a": 0, "b": 1, "c": 2}
    second_cache = {"a": 0, "c": 3, "d": 4}
    with open(first_cache_fpath, "w+") as file:
        json.dump(first_cache, file)
    with open(second_cache_fpath, "w+") as file:
        json.dump(second_cache, file)

    raised = False
    try:
        unify.subtract_cache_files(
            first_cache_fpath,
            second_cache_fpath,
            target_cache_fpath,
        )
    except:
        raised = True
    assert raised, "conflict failed to raise exception"

    unify.subtract_cache_files(
        first_cache_fpath,
        second_cache_fpath,
        target_cache_fpath,
        raise_on_conflict=False,
    )

    with open(target_cache_fpath, "r") as file:
        target_cache = json.load(file)

    assert target_cache == {"b": 1}

    os.remove(first_cache_fpath)
    os.remove(second_cache_fpath)
    os.remove(target_cache_fpath)


@_handle_project
def test_upstream_cache() -> None:
    client = Unify(
        endpoint="gpt-4o@openai",
    )
    r0 = client.generate(user_message="hello", cache=True, local_cache=False)
    logs = unify.get_logs(context=UPSTREAM_CACHE_CONTEXT_NAME)
    assert len(logs) == 1
    r1 = client.generate(user_message="hello", cache=True, local_cache=False)
    logs = unify.get_logs(context=UPSTREAM_CACHE_CONTEXT_NAME)
    assert len(logs) == 1
    assert r0 == r1


@_handle_project
def test_upstream_cache_write() -> None:
    client = Unify(
        endpoint="gpt-4o@openai",
    )
    client.generate(user_message="hello", cache="write", local_cache=False)
    logs = unify.get_logs(context=UPSTREAM_CACHE_CONTEXT_NAME)
    initial_logs_count = len(logs)
    client.generate(user_message="hello", cache="write", local_cache=False)
    logs = unify.get_logs(context=UPSTREAM_CACHE_CONTEXT_NAME)
    assert len(logs) == initial_logs_count


@_handle_project
def test_upstream_cache_read() -> None:
    client = Unify(
        endpoint="gpt-4o@openai",
    )
    r0 = client.generate(user_message="hello", cache="write", local_cache=False)
    logs = unify.get_logs(context=UPSTREAM_CACHE_CONTEXT_NAME)
    initial_logs_count = len(logs)
    r1 = client.generate(user_message="hello", cache="read", local_cache=False)
    logs = unify.get_logs(context=UPSTREAM_CACHE_CONTEXT_NAME)
    assert len(logs) == initial_logs_count
    assert r0 == r1


@_handle_project
def test_upstream_cache_read_only() -> None:
    client = Unify(
        endpoint="gpt-4o@openai",
    )
    r0 = client.generate(user_message="hello", cache="write", local_cache=False)
    logs = unify.get_logs(context=UPSTREAM_CACHE_CONTEXT_NAME)
    initial_logs_count = len(logs)
    r1 = client.generate(user_message="hello", cache="read-only", local_cache=False)
    logs = unify.get_logs(context=UPSTREAM_CACHE_CONTEXT_NAME)
    assert len(logs) == initial_logs_count
    assert r0 == r1

    # Test that read-only mode raises exception when cache doesn't exist
    with pytest.raises(Exception):
        client.generate(
            user_message="new_message",
            cache="read-only",
            local_cache=False,
        )


@_handle_project
def test_upstream_cache_closest_match_on_exception():
    client = Unify(
        endpoint="gpt-4o@openai",
    )
    r0 = client.generate(user_message="hello", cache="both", local_cache=False)
    logs = unify.get_logs(context=UPSTREAM_CACHE_CONTEXT_NAME)
    initial_logs_count = len(logs)
    r1 = client.generate(user_message="helloo", cache="read-closest", local_cache=False)
    logs = unify.get_logs(context=UPSTREAM_CACHE_CONTEXT_NAME)
    assert len(logs) == initial_logs_count
    assert r0 == r1


def test_cached_decorator_both_mode():

    @unify.cached(mode="both")
    def add_two_numbers(x, y):
        time.sleep(1)
        return x + y

    with _CacheHandler():
        t0 = time.perf_counter()
        z1 = add_two_numbers(1, 2)
        t1 = time.perf_counter()
        z2 = add_two_numbers(1, 2)
        t2 = time.perf_counter()

    assert z1 == z2 == 3
    assert t1 - t0 > 1
    assert t2 - t1 < 0.1


@pytest.mark.asyncio
async def test_cached_decorator_async():
    @unify.cached
    async def add_two_numbers(x, y):
        await asyncio.sleep(1)
        return x + y

    with _CacheHandler() as cache_handler:
        t0 = time.perf_counter()
        z1 = await add_two_numbers(1, 2)
        t0 = time.perf_counter() - t0

        assert os.path.exists(cache_handler.test_path)
        mt1 = os.path.getmtime(cache_handler.test_path)

        t1 = time.perf_counter()
        z2 = await add_two_numbers(1, 2)
        t1 = time.perf_counter() - t1
        mt2 = os.path.getmtime(cache_handler.test_path)

        assert mt2 == mt1
        assert t1 < t0
        assert z1 == z2 == 3


@_handle_project
def test_cached_decorator_upstream_cache():
    @unify.cached(local=False)
    def add_two_numbers(x, y):
        return x + y

    add_two_numbers(1, 2)
    logs = unify.get_logs(context=UPSTREAM_CACHE_CONTEXT_NAME)
    assert len(logs) == 1


@_handle_project
@pytest.mark.asyncio
async def test_cached_decorator_upstream_cache_async():
    @unify.cached(local=False)
    async def add_two_numbers(x, y):
        return x + y

    await add_two_numbers(1, 2)
    logs = unify.get_logs(context=UPSTREAM_CACHE_CONTEXT_NAME)
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_cached_decorator_mode_read_only_async():
    @unify.cached(mode="read-only")
    async def add_two_numbers(x, y):
        return x + y

    with _CacheHandler():
        with pytest.raises(Exception):
            await add_two_numbers(1, 2)


@pytest.mark.asyncio
async def test_cached_decorator_mode_read_async():
    @unify.cached(mode="read")
    async def add_two_numbers(x, y):
        return x + y

    with _CacheHandler() as cache_handler:
        r0 = await add_two_numbers(1, 2)
        assert os.path.exists(cache_handler.test_path)
        mt1 = os.path.getmtime(cache_handler.test_path)
        r1 = await add_two_numbers(1, 2)
        mt2 = os.path.getmtime(cache_handler.test_path)
        assert mt2 == mt1
        assert r0 == r1


@pytest.mark.asyncio
async def test_cached_decorator_mode_write_async():
    @unify.cached(mode="write")
    async def add_two_numbers(x, y):
        return x + y

    with _CacheHandler() as cache_handler:
        await add_two_numbers(1, 2)
        assert os.path.exists(cache_handler.test_path)
        mt1 = os.path.getmtime(cache_handler.test_path)
        await asyncio.gather(
            *[add_two_numbers(1, 2) for _ in range(100)],
        )
        mt2 = os.path.getmtime(cache_handler.test_path)
        assert mt2 > mt1


def test_cached_decorator_mode_read():
    @unify.cached(mode="read")
    def add_two_numbers(x, y):
        return x + y

    with _CacheHandler() as cache_handler:
        t0 = time.perf_counter()
        r0 = add_two_numbers(1, 1)
        mt1 = os.path.getmtime(cache_handler.test_path)
        t0 = time.perf_counter() - t0
        t1 = time.perf_counter()
        r1 = add_two_numbers(1, 1)
        t1 = time.perf_counter() - t1
        mt2 = os.path.getmtime(cache_handler.test_path)
        assert mt1 == mt2
        assert t1 < t0
        assert r0 == r1


def test_cached_decorator_mode_read_only():
    @unify.cached(mode="read-only")
    def add_two_numbers(x, y):
        return x + y

    with _CacheHandler():
        with pytest.raises(Exception):
            add_two_numbers(1, 1)


def test_cached_decorator_mode_read_closest():
    @unify.cached(mode="write")
    def squared(y):
        return y * y * 2

    @unify.cached(mode="read-closest")
    def square(x):
        return x * x

    with _CacheHandler() as cache_handler:
        r0 = squared(1)
        assert os.path.exists(cache_handler.test_path)
        mt1 = os.path.getmtime(cache_handler.test_path)

        r1 = square(2)
        mt2 = os.path.getmtime(cache_handler.test_path)
        assert mt2 == mt1
        assert r0 == r1


def test_cached_decorator_mode_write():
    @unify.cached(mode="write")
    def square(x):
        time.sleep(0.5)
        return x * x

    with _CacheHandler() as cache_handler:
        square(1)
        assert os.path.exists(cache_handler.test_path)
        mt1 = os.path.getmtime(cache_handler.test_path)

        square(1)
        mt2 = os.path.getmtime(cache_handler.test_path)
        assert mt2 > mt1


if __name__ == "__main__":
    pass
