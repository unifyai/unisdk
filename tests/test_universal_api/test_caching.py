import os
import time

from unify import Unify
from unify.universal_api._caching import _cache_fpath


def test_basic_caching() -> None:
    if os.path.exists(_cache_fpath):
        os.remove(_cache_fpath)
    client = Unify(
        endpoint="llama-3-8b-chat@together-ai",
    )
    t = time.perf_counter()
    r0 = client.generate(user_message="hello", cache=True)
    t0 = time.perf_counter() - t
    assert os.path.exists(_cache_fpath)
    t = time.perf_counter()
    r1 = client.generate(user_message="hello", cache=True)
    t1 = time.perf_counter() - t
    assert t1 < t0
    assert r0 == r1
    os.remove(_cache_fpath)


if __name__ == "__main__":
    pass
