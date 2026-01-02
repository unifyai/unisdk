import asyncio
import functools
import os
import sys
import traceback
from os import sep

import unify
from unify.utils.caching import LocalCache


def _project_name(fn) -> str:
    """Generate a unique project name from the test's full path.

    Returns names like 'tests/test_logs/test_create_context' to ensure
    uniqueness across the entire test suite, not just within a single file.
    """
    file_path = fn.__code__.co_filename
    fn_name = fn.__name__
    parts = file_path.split(f"{sep}tests{sep}")
    if len(parts) > 1:
        # Extract path relative to tests/, remove .py extension
        test_path = "/".join(parts[1].split(sep))[:-3]
        return f"tests/{test_path}/{fn_name}"
    return fn_name


def _handle_project(test_fn):
    # noinspection PyBroadException
    @functools.wraps(test_fn)
    def wrapper(*args, **kwargs):
        project = _project_name(test_fn)
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
        project = _project_name(test_fn)
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
