import concurrent.futures

import pytest
import unify
from unify.utils.http import RequestError

from ..helpers import _handle_project


def test_project():
    name = "my_project"
    if name in unify.list_projects():
        unify.delete_project(name)
    assert name not in unify.list_projects()
    unify.create_project(name)
    assert name in unify.list_projects()
    unify.delete_project(name)
    assert name not in unify.list_projects()


def test_project_thread_lock():
    # all 10 threads would try to create the project at the same time without
    # thread locking, but only one should acquire the lock, and this should pass
    unify.map(
        unify.log,
        project="test_project",
        a=[1] * 10,
        b=[2] * 10,
        c=[3] * 10,
        from_args=True,
    )
    unify.delete_project("test_project")


@_handle_project
def test_delete_project_contexts():
    unify.create_context("foo")
    unify.create_context("bar")

    assert len(unify.get_contexts()) == 2
    unify.delete_project_contexts("test_delete_project_contexts")

    assert len(unify.get_contexts()) == 0
    assert "test_delete_project_contexts" in unify.list_projects()


def test_create_project_exist_ok_true():
    """Test that exist_ok=True (default) silently succeeds when project already exists."""
    name = "test_exist_ok_true_project"
    if name in unify.list_projects():
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
        if name in unify.list_projects():
            unify.delete_project(name)


def test_create_project_exist_ok_false():
    """Test that exist_ok=False raises an error when project already exists."""
    name = "test_exist_ok_false_project"
    if name in unify.list_projects():
        unify.delete_project(name)

    try:
        unify.create_project(name)
        assert name in unify.list_projects()

        # Second call should raise an error
        with pytest.raises(RequestError) as exc_info:
            unify.create_project(name, exist_ok=False)

        assert "already exists" in str(exc_info.value)
    finally:
        if name in unify.list_projects():
            unify.delete_project(name)


def test_create_project_concurrent_with_exist_ok():
    """Test that concurrent creation with exist_ok=True handles race conditions."""
    name = "test_concurrent_exist_ok_project"
    if name in unify.list_projects():
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
        if name in unify.list_projects():
            unify.delete_project(name)


def test_delete_project_missing_ok_true():
    """Test that missing_ok=True (default) silently succeeds when project does not exist."""
    name = "test_missing_ok_true_project"
    if name in unify.list_projects():
        unify.delete_project(name)

    assert name not in unify.list_projects()

    # Delete non-existent project should succeed without error
    result = unify.delete_project(name)
    assert result is None

    # Still no project
    assert name not in unify.list_projects()


def test_delete_project_missing_ok_false():
    """Test that missing_ok=False raises an error when project does not exist."""
    name = "test_missing_ok_false_project"
    if name in unify.list_projects():
        unify.delete_project(name)

    assert name not in unify.list_projects()

    # Delete non-existent project should raise an error
    with pytest.raises(RequestError) as exc_info:
        unify.delete_project(name, missing_ok=False)

    assert "not found" in str(exc_info.value).lower()


def test_delete_project_concurrent_with_missing_ok():
    """Test that concurrent deletion with missing_ok=True handles race conditions."""
    name = "test_concurrent_missing_ok_project"
    if name in unify.list_projects():
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
