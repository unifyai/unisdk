import unify
from ..helpers import _handle_project


@_handle_project
def test_get_contexts():
    assert len(unify.get_contexts()) == 0
    unify.log(x=0, context="a/b")
    unify.log(x=1, context="a/b")
    unify.log(x=0, context="b/c")
    unify.log(x=1, context="b/c")
    contexts = unify.get_contexts()
    assert len(contexts) == 2
    assert "a/b" in contexts
    assert "b/c" in contexts
    contexts = unify.get_contexts(prefix="a")
    assert len(contexts) == 1
    assert "a/b" in contexts
    assert "a/c" not in contexts
    contexts = unify.get_contexts(prefix="b")
    assert len(contexts) == 1
    assert "b/c" in contexts
    assert "a/b" not in contexts


if __name__ == "__main__":
    pass
