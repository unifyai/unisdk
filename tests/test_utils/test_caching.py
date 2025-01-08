import os
import time

import unify
from unify import Unify
from unify.utils._caching import _cache_fpath


# noinspection PyBroadException
def test_basic_caching() -> None:
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
        t = time.perf_counter()
        r1 = client.generate(user_message="hello", cache=True)
        t1 = time.perf_counter() - t
        assert t1 < t0
        assert r0 == r1
        os.remove(local_cache_path)
        global_cache_path = local_cache_path.replace(".test_cache.json", ".cache.json")
        unify.utils._caching._cache_fpath = global_cache_path
    except:
        if os.path.exists(local_cache_path):
            os.remove(local_cache_path)


if __name__ == "__main__":
    pass
