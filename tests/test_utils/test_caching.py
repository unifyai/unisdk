import json
import os
import time
import traceback

import pytest
import unify
from tests.test_utils.helpers import _CacheHandler
from unify import Unify


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


if __name__ == "__main__":
    pass
