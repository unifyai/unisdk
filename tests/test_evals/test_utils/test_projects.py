import unify


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
    unify.map(unify.log, project="test_project", a=[1] * 10, b=[2] * 10, c=[3] * 10)
    unify.delete_project("test_project")


if __name__ == "__main__":
    pass
