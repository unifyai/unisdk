import os
import time

import unify
from unify import Unify
from unify.utils._caching import _cache_fpath


# noinspection PyBroadException
def test_cache() -> None:
    local_cache_path = _cache_fpath.replace(".cache.json", ".test_cache.json")
    try:
        unify.utils._caching._cache_fpath = local_cache_path
        if os.path.exists(local_cache_path):
            os.remove(local_cache_path)
        client = Unify(
            endpoint="gpt-4o@openai",
        )
        t = time.perf_counter()
        r0 = client.generate(user_message="hello", cache=True)
        t0 = time.perf_counter() - t
        assert os.path.exists(local_cache_path)
        mt0 = os.path.getmtime(local_cache_path)
        t = time.perf_counter()
        r1 = client.generate(user_message="hello", cache=True)
        mt1 = os.path.getmtime(local_cache_path)
        t1 = time.perf_counter() - t
        assert t1 < t0
        assert mt0 == mt1
        assert r0 == r1
        os.remove(local_cache_path)
        unify.utils._caching._cache_fpath = _cache_fpath
    except Exception as e:
        unify.utils._caching._cache_fpath = _cache_fpath
        if os.path.exists(local_cache_path):
            os.remove(local_cache_path)
        raise e


# noinspection PyBroadException
def test_cache_write() -> None:
    local_cache_path = _cache_fpath.replace(".cache.json", ".test_cache.json")
    try:
        unify.utils._caching._cache_fpath = local_cache_path
        if os.path.exists(local_cache_path):
            os.remove(local_cache_path)
        client = Unify(
            endpoint="gpt-4o@openai",
        )
        client.generate(user_message="hello", cache="write")
        assert os.path.exists(local_cache_path)
        mt0 = os.path.getmtime(local_cache_path)
        client.generate(user_message="hello", cache="write")
        mt1 = os.path.getmtime(local_cache_path)
        assert mt0 < mt1
        os.remove(local_cache_path)
        unify.utils._caching._cache_fpath = _cache_fpath
    except Exception as e:
        unify.utils._caching._cache_fpath = _cache_fpath
        if os.path.exists(local_cache_path):
            os.remove(local_cache_path)
        raise e


# noinspection PyBroadException
def test_cache_read() -> None:
    local_cache_path = _cache_fpath.replace(".cache.json", ".test_cache.json")
    try:
        unify.utils._caching._cache_fpath = local_cache_path
        if os.path.exists(local_cache_path):
            os.remove(local_cache_path)
        client = Unify(
            endpoint="gpt-4o@openai",
        )
        t = time.perf_counter()
        r0 = client.generate(user_message="hello", cache="write")
        t0 = time.perf_counter() - t
        assert os.path.exists(local_cache_path)
        mt0 = os.path.getmtime(local_cache_path)
        t = time.perf_counter()
        r1 = client.generate(user_message="hello", cache="read")
        mt1 = os.path.getmtime(local_cache_path)
        t1 = time.perf_counter() - t
        assert t1 < t0
        assert mt0 == mt1
        assert r0 == r1
        os.remove(local_cache_path)
        unify.utils._caching._cache_fpath = _cache_fpath
    except Exception as e:
        unify.utils._caching._cache_fpath = _cache_fpath
        if os.path.exists(local_cache_path):
            os.remove(local_cache_path)
        raise e


# noinspection PyBroadException
def test_cache_read_only() -> None:
    local_cache_path = _cache_fpath.replace(".cache.json", ".test_cache.json")
    try:
        unify.utils._caching._cache_fpath = local_cache_path
        if os.path.exists(local_cache_path):
            os.remove(local_cache_path)
        client = Unify(
            endpoint="gpt-4o@openai",
        )
        t = time.perf_counter()
        r0 = client.generate(user_message="hello", cache="write")
        t0 = time.perf_counter() - t
        assert os.path.exists(local_cache_path)
        mt0 = os.path.getmtime(local_cache_path)
        t = time.perf_counter()
        r1 = client.generate(user_message="hello", cache="read-only")
        mt1 = os.path.getmtime(local_cache_path)
        t1 = time.perf_counter() - t
        assert t1 < t0
        assert mt0 == mt1
        assert r0 == r1
        os.remove(local_cache_path)
        unify._caching._cache = None
        try:
            client.generate(user_message="hello", cache="read-only")
            raised_exception = False
        except Exception:
            raised_exception = True
        assert raised_exception, "read-only mode should have raised exception"
        unify.utils._caching._cache_fpath = _cache_fpath
    except Exception as e:
        unify.utils._caching._cache_fpath = _cache_fpath
        if os.path.exists(local_cache_path):
            os.remove(local_cache_path)
        raise e


if __name__ == "__main__":
    pass
