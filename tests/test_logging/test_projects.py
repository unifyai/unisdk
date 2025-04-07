import os

import unify


def test_set_project():
    unify.deactivate()
    assert unify.active_project() is None
    unify.activate("my_project")
    assert unify.active_project() == "my_project"
    unify.deactivate()


def test_unset_project():
    unify.deactivate()
    assert unify.active_project() is None
    unify.activate("my_project")
    assert unify.active_project() == "my_project"
    unify.deactivate()
    assert unify.active_project() is None


def test_with_project():
    unify.deactivate()
    assert unify.active_project() is None
    with unify.Project("my_project"):
        assert unify.active_project() == "my_project"
    assert unify.active_project() is None


def test_set_project_then_log():
    unify.deactivate()
    assert unify.active_project() is None
    unify.activate("test_set_project_then_log")
    assert unify.active_project() == "test_set_project_then_log"
    unify.log(key=1.0)
    unify.deactivate()
    assert unify.active_project() is None
    unify.delete_project("test_set_project_then_log")


def test_with_project_then_log():
    unify.deactivate()
    assert unify.active_project() is None
    with unify.Project("test_with_project_then_log"):
        assert unify.active_project() == "test_with_project_then_log"
        unify.log(key=1.0)
    assert unify.active_project() is None
    unify.delete_project("test_with_project_then_log")


def test_project_env_var():
    unify.deactivate()
    assert unify.active_project() is None
    os.environ["UNIFY_PROJECT"] = "test_project_env_var"
    assert unify.active_project() == "test_project_env_var"
    unify.log(x=0, y=1, z=2)
    del os.environ["UNIFY_PROJECT"]
    assert unify.active_project() is None
    logs = unify.get_logs(project="test_project_env_var")
    assert len(logs) == 1
    assert logs[0].entries == {"x": 0, "y": 1, "z": 2}
    unify.delete_project("test_project_env_var")


if __name__ == "__main__":
    pass
