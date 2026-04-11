import concurrent.futures
import uuid
from datetime import datetime

import pytest

import unify
from unify.utils import http


def _unique_project_name(base: str) -> str:
    """Generate a unique project name with datetime and random suffix for concurrency safety."""
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3]
    random_suffix = uuid.uuid4().hex[:4]
    return f"{base}_{timestamp}_{random_suffix}"


# =============================================================================
# Basic project tests
# =============================================================================


def test_set_project(monkeypatch):
    """Test setting the active project via unify.activate()."""
    name = _unique_project_name("test_set_project")
    # Use monkeypatch to isolate unify.PROJECT mutations
    monkeypatch.setattr(unify, "PROJECT", None)
    try:
        assert unify.active_project() is None
        unify.activate(name)
        assert unify.active_project() == name
    finally:
        unify.delete_project(name)


def test_set_project_then_log(monkeypatch):
    """Test setting project and logging to it."""
    name = _unique_project_name("test_set_project_then_log")
    # Use monkeypatch to isolate unify.PROJECT mutations
    monkeypatch.setattr(unify, "PROJECT", None)
    try:
        assert unify.active_project() is None
        unify.activate(name)
        assert unify.active_project() == name
        unify.log(key=1.0)
    finally:
        unify.delete_project(name)


def test_project_env_var(monkeypatch):
    """Test that UNIFY_PROJECT environment variable sets the active project."""
    name = _unique_project_name("test_project_env_var")
    # Use monkeypatch to isolate both unify.PROJECT and env var mutations
    monkeypatch.setattr(unify, "PROJECT", None)
    monkeypatch.delenv("UNIFY_PROJECT", raising=False)
    try:
        assert unify.active_project() is None
        monkeypatch.setenv("UNIFY_PROJECT", name)
        assert unify.active_project() == name
        unify.delete_project(name)
        unify.create_project(name)
        unify.log(x=0, y=1, z=2)
        monkeypatch.delenv("UNIFY_PROJECT")
        assert unify.active_project() is None
        logs = unify.get_logs(project=name)
        assert len(logs) == 1
        assert logs[0].entries == {"x": 0, "y": 1, "z": 2}
    finally:
        unify.delete_project(name)


# =============================================================================
# Project CRUD tests
# =============================================================================


def test_project():
    name = _unique_project_name("test_project")
    unify.delete_project(name)
    assert name not in unify.list_projects()
    unify.create_project(name)
    assert name in unify.list_projects()
    unify.delete_project(name)
    assert name not in unify.list_projects()


def test_project_thread_lock():
    name = _unique_project_name("test_project_thread_lock")
    try:
        # all 10 threads would try to create the project at the same time without
        # thread locking, but only one should acquire the lock, and this should pass
        unify.map(
            unify.log,
            project=name,
            a=[1] * 10,
            b=[2] * 10,
            c=[3] * 10,
            from_args=True,
        )
    finally:
        unify.delete_project(name)


def test_delete_project_contexts():
    name = _unique_project_name("test_delete_project_contexts")
    try:
        unify.create_project(name)
        unify.create_context("foo", project=name)
        unify.create_context("bar", project=name)

        assert len(unify.get_contexts(project=name)) == 2
        unify.delete_project_contexts(name)

        assert len(unify.get_contexts(project=name)) == 0
        assert name in unify.list_projects()
    finally:
        unify.delete_project(name)


def test_create_project_exist_ok_true():
    """Test that exist_ok=True (default) silently succeeds when project already exists."""
    name = _unique_project_name("test_exist_ok_true")
    unify.delete_project(name)

    try:
        unify.create_project(name)
        assert name in unify.list_projects()

        # Second call should succeed without error
        result = unify.create_project(name)
        assert result is None

        # Project should still exist
        assert name in unify.list_projects()
    finally:
        unify.delete_project(name)


def test_create_project_exist_ok_false():
    """Test that exist_ok=False raises an error when project already exists."""
    name = _unique_project_name("test_exist_ok_false")
    unify.delete_project(name)

    try:
        unify.create_project(name)
        assert name in unify.list_projects()

        # Second call should raise an error
        with pytest.raises(http.RequestError) as exc_info:
            unify.create_project(name, exist_ok=False)

        assert "already exists" in str(exc_info.value)
    finally:
        unify.delete_project(name)


def test_create_project_concurrent_with_exist_ok():
    """Test that concurrent creation with exist_ok=True handles race conditions."""
    name = _unique_project_name("test_concurrent_exist_ok")
    unify.delete_project(name)

    try:
        num_workers = 10

        def create_project_task():
            return unify.create_project(name)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(create_project_task) for _ in range(num_workers)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All calls should complete without raising an exception
        assert len(results) == num_workers

        # Project should exist
        assert name in unify.list_projects()
    finally:
        unify.delete_project(name)


def test_delete_project_missing_ok_true():
    """Test that missing_ok=True (default) silently succeeds when project does not exist."""
    name = _unique_project_name("test_missing_ok_true")
    unify.delete_project(name)

    assert name not in unify.list_projects()

    # Delete non-existent project should succeed without error
    result = unify.delete_project(name)
    assert result is None

    # Still no project
    assert name not in unify.list_projects()


def test_delete_project_missing_ok_false():
    """Test that missing_ok=False raises an error when project does not exist."""
    name = _unique_project_name("test_missing_ok_false")
    unify.delete_project(name)

    assert name not in unify.list_projects()

    # Delete non-existent project should raise an error
    with pytest.raises(http.RequestError) as exc_info:
        unify.delete_project(name, missing_ok=False)

    assert "not found" in str(exc_info.value).lower()


def test_delete_project_concurrent_with_missing_ok():
    """Test that concurrent deletion with missing_ok=True handles race conditions."""
    name = _unique_project_name("test_concurrent_missing_ok")
    unify.delete_project(name)

    unify.create_project(name)
    assert name in unify.list_projects()

    num_workers = 10

    def delete_project_task():
        return unify.delete_project(name)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(delete_project_task) for _ in range(num_workers)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # All calls should complete without raising an exception
    assert len(results) == num_workers

    # Project should no longer exist
    assert name not in unify.list_projects()


if __name__ == "__main__":
    pass
