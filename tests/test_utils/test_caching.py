import os
import time
import traceback

import pytest
import unify
from unify import Unify
from unify.utils._caching import _get_caching_fpath


class _CacheHandler:
    def __init__(self):
        self._old_cache_fpath = _get_caching_fpath()
        self._fname = ".test_cache.json"
        self.test_path = ""

    def __enter__(self):
        unify.set_caching_fname(self._fname)
        self.test_path = _get_caching_fpath()
        if os.path.exists(self.test_path):
            os.remove(self.test_path)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if os.path.exists(self.test_path):
            os.remove(self.test_path)
        unify.set_caching_fname(self._old_cache_fpath)


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


if __name__ == "__main__":
    pass
