import unify
from ..helpers import _handle_project


@_handle_project
def test_contexts():
    assert len(unify.get_contexts()) == 0
    unify.log(x=0, context="a/b")
    unify.log(x=1, context="a/b")
    unify.log(x=0, context="a/c")
    unify.log(x=1, context="a/c")
    contexts = unify.get_contexts()
    assert len(contexts) == 2
    assert "a/b" in contexts
    assert "a/c" in contexts


if __name__ == "__main__":
    pass
