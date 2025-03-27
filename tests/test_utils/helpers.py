import os

import unify
from unify.utils._caching import _get_caching_fpath


class _CacheHandler:
    def __init__(self, fname=".test_cache.json"):
        self._old_cache_fpath = _get_caching_fpath()
        self._fname = fname
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
