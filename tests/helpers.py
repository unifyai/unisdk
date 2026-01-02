import asyncio
import functools
import os
import sys
import traceback

import unify
from unify.utils.caching import LocalCache


def _handle_project(test_fn):
    # noinspection PyBroadException
    @functools.wraps(test_fn)
    def wrapper(*args, **kwargs):
        project = test_fn.__name__
        if project in unify.list_projects():
            unify.delete_project(project)
        try:
            unify.activate(project)
            unify.unset_context()
            test_fn(*args, **kwargs)
            unify.delete_project(project)
        except:
            unify.delete_project(project)
            exc_type, exc_value, exc_tb = sys.exc_info()
            tb_string = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            raise Exception(f"{tb_string}")

    @functools.wraps(test_fn)
    async def async_wrapper(*args, **kwargs):
        project = test_fn.__name__
        if project in unify.list_projects():
            unify.delete_project(project)
        try:
            unify.activate(project)
            unify.unset_context()
            await test_fn(*args, **kwargs)
            unify.delete_project(project)
        except:
            unify.delete_project(project)
            exc_type, exc_value, exc_tb = sys.exc_info()
            tb_string = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            raise Exception(f"{tb_string}")

    return async_wrapper if asyncio.iscoroutinefunction(test_fn) else wrapper


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
