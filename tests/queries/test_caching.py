import os
import time
import unittest

from unify import Unify
from unify._caching import _cache_fpath


class TestUnifyCaching(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_api_key = os.environ.get("UNIFY_KEY")

    # Basic #
    # ------#

    def test_basic_caching(self) -> None:
        if os.path.exists(_cache_fpath):
            os.remove(_cache_fpath)
        client = Unify(
            api_key=self.valid_api_key, endpoint="llama-3-8b-chat@together-ai"
        )
        t = time.perf_counter()
        r0 = client.generate(user_prompt="hello", cache=True)
        t0 = time.perf_counter() - t
        self.assertTrue(os.path.exists(_cache_fpath))
        t = time.perf_counter()
        r1 = client.generate(user_prompt="hello", cache=True)
        t1 = time.perf_counter() - t
        self.assertLess(t1, t0)
        self.assertEqual(r0, r1)
        os.remove(_cache_fpath)


if __name__ == "__main__":
    unittest.main()
