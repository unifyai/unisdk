import unify

from ..helpers import _handle_project


@_handle_project
def test_create_context():
    assert len(unify.get_contexts()) == 0
    unify.create_context("my_context")
    assert len(unify.get_contexts()) == 1
    assert "my_context" in unify.get_contexts()


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


@_handle_project
def test_delete_context():
    unify.log(x=0, context="a/b")
    contexts = unify.get_contexts()
    assert len(contexts) == 1
    assert "a/b" in contexts
    unify.delete_context("a/b")
    assert "a/b" not in unify.get_contexts()
    assert len(unify.get_logs()) == 0


@_handle_project
def test_add_logs_to_context():
    l0 = unify.log(x=0, context="a/b")
    l1 = unify.log(x=1, context="a/b")
    l2 = unify.log(x=2, context="b/c")
    l3 = unify.log(x=3, context="b/c")
    unify.add_logs_to_context(log_ids=[l0.id, l1.id], context="b/c")
    assert len(unify.get_logs(context="a/b")) == 2
    assert unify.get_logs(context="a/b", return_ids_only=True) == [l1.id, l0.id]
    assert len(unify.get_logs(context="b/c")) == 4
    assert unify.get_logs(context="b/c", return_ids_only=True) == [
        l3.id,
        l2.id,
        l1.id,
        l0.id,
    ]


@_handle_project
def test_rename_context():
    unify.log(x=0, context="a/b")
    unify.rename_context("a/b", "a/c")
    contexts = unify.get_contexts()
    assert "a/b" not in contexts
    assert "a/c" in contexts
    logs = unify.get_logs(context="a/c")
    assert len(logs) == 1
    assert logs[0].context == "a/c"


@_handle_project
def test_get_context():
    name = "foo"
    desc = "my_description"
    is_versioned = True
    allow_duplicates = True
    unify.create_context(
        name,
        description=desc,
        is_versioned=is_versioned,
        allow_duplicates=allow_duplicates,
    )

    context = unify.get_context(name)
    assert context["name"] == name
    assert context["description"] == desc
    assert context["is_versioned"] is is_versioned
    assert context["allow_duplicates"] is allow_duplicates


@_handle_project
def test_context_nesting():
    current_ctx = unify.get_active_context()
    assert current_ctx["read"] == ""
    assert current_ctx["write"] == ""

    with unify.Context("A"):
        current_ctx = unify.get_active_context()
        assert current_ctx["read"] == "A"
        assert current_ctx["write"] == "A"
        assert unify.get_context(current_ctx["read"])["name"] == "A"
        assert unify.get_context(current_ctx["write"])["name"] == "A"

        with unify.Context("B"):
            current_ctx = unify.get_active_context()
            assert current_ctx["read"] == "A/B"
            assert current_ctx["write"] == "A/B"
            assert unify.get_context(current_ctx["read"])["name"] == "A/B"
            assert unify.get_context(current_ctx["write"])["name"] == "A/B"

    current_ctx = unify.get_active_context()
    assert current_ctx["read"] == ""
    assert current_ctx["write"] == ""


@_handle_project
def test_context_relative():
    unify.set_context("A", relative=True)

    unify.set_context("B", relative=True)
    current_ctx = unify.get_active_context()
    assert current_ctx["read"] == "A/B"
    assert current_ctx["write"] == "A/B"
    assert unify.get_context(current_ctx["read"])["name"] == "A/B"

    unify.set_context("C", relative=True)
    current_ctx = unify.get_active_context()
    assert current_ctx["read"] == "A/B/C"
    assert current_ctx["write"] == "A/B/C"
    assert unify.get_context(current_ctx["read"])["name"] == "A/B/C"


@_handle_project
def test_context_not_relative():
    unify.set_context("A", relative=False)
    current_ctx = unify.get_active_context()
    assert current_ctx["read"] == "A"
    assert current_ctx["write"] == "A"
    assert unify.get_context(current_ctx["read"])["name"] == "A"

    unify.set_context("B", relative=False)
    current_ctx = unify.get_active_context()
    assert current_ctx["read"] == "B"
    assert current_ctx["write"] == "B"
    assert unify.get_context(current_ctx["read"])["name"] == "B"


if __name__ == "__main__":
    pass
