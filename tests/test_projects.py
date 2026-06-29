import concurrent.futures
import uuid
from datetime import datetime

import pytest

import unisdk
from unisdk.utils import http


def _unique_project_name(base: str) -> str:
    """Generate a unique project name with datetime and random suffix for concurrency safety."""
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3]
    random_suffix = uuid.uuid4().hex[:4]
    return f"{base}_{timestamp}_{random_suffix}"


# =============================================================================
# Basic project tests
# =============================================================================


def test_set_project(monkeypatch):
    """Test setting the active project via unisdk.activate()."""
    name = _unique_project_name("test_set_project")
    # Use monkeypatch to isolate unisdk.PROJECT mutations
    monkeypatch.setattr(unify, "PROJECT", None)
    try:
        assert unisdk.active_project() is None
        unisdk.activate(name)
        assert unisdk.active_project() == name
    finally:
        unisdk.delete_project(name)


def test_set_project_then_log(monkeypatch):
    """Test setting project and logging to it."""
    name = _unique_project_name("test_set_project_then_log")
    # Use monkeypatch to isolate unisdk.PROJECT mutations
    monkeypatch.setattr(unify, "PROJECT", None)
    try:
        assert unisdk.active_project() is None
        unisdk.activate(name)
        assert unisdk.active_project() == name
        unisdk.log(key=1.0)
    finally:
        unisdk.delete_project(name)


def test_project_env_var(monkeypatch):
    """Test that UNISDK_PROJECT environment variable sets the active project."""
    name = _unique_project_name("test_project_env_var")
    # Use monkeypatch to isolate both unisdk.PROJECT and env var mutations
    monkeypatch.setattr(unify, "PROJECT", None)
    monkeypatch.delenv("UNISDK_PROJECT", raising=False)
    try:
        assert unisdk.active_project() is None
        monkeypatch.setenv("UNISDK_PROJECT", name)
        assert unisdk.active_project() == name
        unisdk.delete_project(name)
        unisdk.create_project(name)
        unisdk.log(x=0, y=1, z=2)
        monkeypatch.delenv("UNISDK_PROJECT")
        assert unisdk.active_project() is None
        logs = unisdk.get_logs(project=name)
        assert len(logs) == 1
        assert logs[0].entries == {"x": 0, "y": 1, "z": 2}
    finally:
        unisdk.delete_project(name)


# =============================================================================
# Project CRUD tests
# =============================================================================


def test_project():
    name = _unique_project_name("test_project")
    unisdk.delete_project(name)
    assert name not in unisdk.list_projects()
    unisdk.create_project(name)
    assert name in unisdk.list_projects()
    unisdk.delete_project(name)
    assert name not in unisdk.list_projects()


def test_project_thread_lock():
    name = _unique_project_name("test_project_thread_lock")
    try:
        # all 10 threads would try to create the project at the same time without
        # thread locking, but only one should acquire the lock, and this should pass
        unisdk.map(
            unisdk.log,
            project=name,
            a=[1] * 10,
            b=[2] * 10,
            c=[3] * 10,
            from_args=True,
        )
    finally:
        unisdk.delete_project(name)


def test_delete_project_contexts():
    name = _unique_project_name("test_delete_project_contexts")
    try:
        unisdk.create_project(name)
        unisdk.create_context("foo", project=name)
        unisdk.create_context("bar", project=name)

        assert len(unisdk.get_contexts(project=name)) == 2
        unisdk.delete_project_contexts(name)

        assert len(unisdk.get_contexts(project=name)) == 0
        assert name in unisdk.list_projects()
    finally:
        unisdk.delete_project(name)


def test_create_project_exist_ok_true():
    """Test that exist_ok=True (default) silently succeeds when project already exists."""
    name = _unique_project_name("test_exist_ok_true")
    unisdk.delete_project(name)

    try:
        unisdk.create_project(name)
        assert name in unisdk.list_projects()

        # Second call should succeed without error
        result = unisdk.create_project(name)
        assert result is None

        # Project should still exist
        assert name in unisdk.list_projects()
    finally:
        unisdk.delete_project(name)


def test_create_project_exist_ok_false():
    """Test that exist_ok=False raises an error when project already exists."""
    name = _unique_project_name("test_exist_ok_false")
    unisdk.delete_project(name)

    try:
        unisdk.create_project(name)
        assert name in unisdk.list_projects()

        # Second call should raise an error
        with pytest.raises(http.RequestError) as exc_info:
            unisdk.create_project(name, exist_ok=False)

        assert "already exists" in str(exc_info.value)
    finally:
        unisdk.delete_project(name)


def test_create_project_concurrent_with_exist_ok():
    """Test that concurrent creation with exist_ok=True handles race conditions."""
    name = _unique_project_name("test_concurrent_exist_ok")
    unisdk.delete_project(name)

    try:
        num_workers = 10

        def create_project_task():
            return unisdk.create_project(name)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(create_project_task) for _ in range(num_workers)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All calls should complete without raising an exception
        assert len(results) == num_workers

        # Project should exist
        assert name in unisdk.list_projects()
    finally:
        unisdk.delete_project(name)


def test_delete_project_missing_ok_true():
    """Test that missing_ok=True (default) silently succeeds when project does not exist."""
    name = _unique_project_name("test_missing_ok_true")
    unisdk.delete_project(name)

    assert name not in unisdk.list_projects()

    # Delete non-existent project should succeed without error
    result = unisdk.delete_project(name)
    assert result is None

    # Still no project
    assert name not in unisdk.list_projects()


def test_delete_project_missing_ok_false():
    """Test that missing_ok=False raises an error when project does not exist."""
    name = _unique_project_name("test_missing_ok_false")
    unisdk.delete_project(name)

    assert name not in unisdk.list_projects()

    # Delete non-existent project should raise an error
    with pytest.raises(http.RequestError) as exc_info:
        unisdk.delete_project(name, missing_ok=False)

    assert "not found" in str(exc_info.value).lower()


def test_delete_project_concurrent_with_missing_ok():
    """Test that concurrent deletion with missing_ok=True handles race conditions."""
    name = _unique_project_name("test_concurrent_missing_ok")
    unisdk.delete_project(name)

    unisdk.create_project(name)
    assert name in unisdk.list_projects()

    num_workers = 10

    def delete_project_task():
        return unisdk.delete_project(name)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(delete_project_task) for _ in range(num_workers)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # All calls should complete without raising an exception
    assert len(results) == num_workers

    # Project should no longer exist
    assert name not in unisdk.list_projects()


if __name__ == "__main__":
    pass
