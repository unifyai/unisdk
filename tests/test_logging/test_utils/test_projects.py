import unify

from ..helpers import _handle_project


def test_project():
    name = "my_project"
    if name in unify.list_projects():
        unify.delete_project(name)
    assert name not in unify.list_projects()
    unify.create_project(name)
    assert name in unify.list_projects()
    new_name = "my_project1"
    unify.rename_project(name, new_name)
    assert new_name in unify.list_projects()
    unify.delete_project(new_name)
    assert new_name not in unify.list_projects()


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
def test_delete_project_logs():
    [unify.log(x=i) for i in range(10)]
    assert len(unify.get_logs()) == 10
    unify.delete_project_logs("test_delete_project_logs")
    assert len(unify.get_logs()) == 0
    assert "test_delete_project_logs" in unify.list_projects()


@_handle_project
def test_delete_project_contexts():
    unify.create_context("foo")
    unify.create_context("bar")

    assert len(unify.get_contexts()) == 2
    unify.delete_project_contexts("test_delete_project_contexts")

    assert len(unify.get_contexts()) == 0
    assert "test_delete_project_contexts" in unify.list_projects()


if __name__ == "__main__":
    pass
