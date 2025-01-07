import pytest

import unify


def test_set_project():
    unify.deactivate()
    assert unify.active_project is None
    unify.activate("my_project")
    assert unify.active_project == "my_project"
    unify.deactivate()


def test_unset_project():
    unify.deactivate()
    assert unify.active_project is None
    unify.activate("my_project")
    assert unify.active_project == "my_project"
    unify.deactivate()
    assert unify.active_project is None


def test_with_project():
    unify.deactivate()
    assert unify.active_project is None
    with unify.Project("my_project"):
        assert unify.active_project == "my_project"
    assert unify.active_project is None


def test_set_project_then_log():
    unify.deactivate()
    assert unify.active_project is None
    unify.activate("my_project")
    assert unify.active_project == "my_project"
    unify.log(key=1.0)
    unify.deactivate()
    assert unify.active_project is None


def test_with_project_then_log():
    unify.deactivate()
    assert unify.active_project is None
    with unify.Project("my_project"):
        assert unify.active_project == "my_project"
        unify.log(key=1.0)
    assert unify.active_project is None


if __name__ == "__main__":
    pass
