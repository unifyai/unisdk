import os

from unify.utils.caching import LocalCache


class _CacheHandler:
    def __init__(self, fname=".test_cache.ndjson"):
        self._old_cache_fpath = LocalCache.get_cache_filepath(fname)
        self._fname = fname
        self.test_path = ""

    def __enter__(self):
        LocalCache.set_cache_name(self._fname)
        self.test_path = LocalCache.get_cache_filepath(self._fname)
        if os.path.exists(self.test_path):
            os.remove(self.test_path)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if os.path.exists(self.test_path):
            os.remove(self.test_path)
        LocalCache.set_cache_name(self._old_cache_fpath)
