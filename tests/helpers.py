import asyncio
import functools
import os
import sys
import traceback
import uuid
from contextvars import ContextVar
from datetime import datetime
from os import sep
from typing import Optional

import unify
from unify.utils.caching import LocalCache

# Single shared project for all tests (analogous to UnityTests in unity repo)
TEST_PROJECT = "UnifyTests"

# Thread/async-safe context variable for test context tracking
# Using ContextVar instead of a module-level list ensures isolation
# when tests run concurrently in the same process (threading/asyncio)
_TEST_CTX: ContextVar[Optional[str]] = ContextVar("test_ctx", default=None)


def get_test_context() -> Optional[str]:
    """Get the current test's unique context path.

    Returns the context path set by @_handle_project, or None if not in a test.
    Tests can use this to create child contexts and filter get_contexts() results.
    """
    return _TEST_CTX.get()


def _context_path(fn) -> str:
    """Generate a context path from the test's full file path.

    Returns paths like 'tests/test_logs/test_create_context' to ensure
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


def _unique_suffix() -> str:
    """Generate a unique suffix combining datetime and random component.

    Uses millisecond timestamp plus 4 random hex chars to prevent collisions
    even when the same test starts multiple times within the same millisecond.
    """
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3]
    random_suffix = uuid.uuid4().hex[:4]
    return f"{timestamp}_{random_suffix}"


def _unique_context(fn) -> str:
    """Generate a unique context name with datetime and random suffix.

    Returns names like 'tests/test_logs/test_foo/2026-01-02T15-30-45-123_a1b2'
    to prevent collisions between concurrent CI runs.
    """
    base_path = _context_path(fn)
    return f"{base_path}/{_unique_suffix()}"


def _ensure_test_project():
    """Ensure the shared test project exists."""
    if TEST_PROJECT not in unify.list_projects():
        unify.create_project(TEST_PROJECT)
    unify.activate(TEST_PROJECT)


def _handle_project(test_fn):
    """Decorator for tests that operate within the shared UnifyTests project.

    Creates a unique context for each test run, enabling concurrent execution.
    Use this for tests that work with logs and nested contexts.
    """

    # noinspection PyBroadException
    @functools.wraps(test_fn)
    def wrapper(*args, **kwargs):
        _ensure_test_project()
        ctx = _unique_context(test_fn)
        token = _TEST_CTX.set(ctx)
        unify.set_context(ctx, relative=False)
        try:
            test_fn(*args, **kwargs)
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            tb_string = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            raise Exception(f"{tb_string}")
        finally:
            _TEST_CTX.reset(token)
            unify.delete_context(ctx, delete_children=True)
            unify.unset_context()

    @functools.wraps(test_fn)
    async def async_wrapper(*args, **kwargs):
        _ensure_test_project()
        ctx = _unique_context(test_fn)
        token = _TEST_CTX.set(ctx)
        unify.set_context(ctx, relative=False)
        try:
            await test_fn(*args, **kwargs)
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            tb_string = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            raise Exception(f"{tb_string}")
        finally:
            _TEST_CTX.reset(token)
            unify.delete_context(ctx, delete_children=True)
            unify.unset_context()

    return async_wrapper if asyncio.iscoroutinefunction(test_fn) else wrapper


def _unique_project(fn) -> str:
    """Generate a unique project name with datetime and random suffix."""
    base_path = _context_path(fn)
    # Replace / with _ for valid project name
    return f"{base_path}/{_unique_suffix()}".replace("/", "_")


def _handle_project_isolated(test_fn):
    """Decorator for tests that need their own isolated project.

    Creates a unique project per test run, providing complete isolation.
    Use this for tests that operate on project-level context operations
    (create_context at root, get_contexts for whole project, etc.).
    """

    # noinspection PyBroadException
    @functools.wraps(test_fn)
    def wrapper(*args, **kwargs):
        project = _unique_project(test_fn)
        # Project name is unique (timestamp + random), so it won't exist yet
        unify.activate(project)
        unify.unset_context()
        try:
            test_fn(*args, **kwargs)
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            tb_string = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            raise Exception(f"{tb_string}")
        finally:
            unify.delete_project(project)

    @functools.wraps(test_fn)
    async def async_wrapper(*args, **kwargs):
        project = _unique_project(test_fn)
        # Project name is unique (timestamp + random), so it won't exist yet
        unify.activate(project)
        unify.unset_context()
        try:
            await test_fn(*args, **kwargs)
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            tb_string = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            raise Exception(f"{tb_string}")
        finally:
            unify.delete_project(project)

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
