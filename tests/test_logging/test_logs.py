import asyncio
import threading

import pytest
import unify

from .helpers import _handle_project

# Context Handlers #
# -----------------#

# Log


@_handle_project
def test_with_log():

    with unify.Log(a="a"):
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].entries == {"a": "a"}
        unify.add_log_entries(b="b", c="c")
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].entries == {"a": "a", "b": "b", "c": "c"}
        with unify.Log(d="d"):
            logs = unify.get_logs()
            assert len(logs) == 2
            assert logs[0].entries == {"d": "d"}
            unify.add_log_entries(e="e", f="f")
            logs = unify.get_logs()
            assert len(logs) == 2
            assert logs[0].entries == {"d": "d", "e": "e", "f": "f"}
        unify.add_log_entries(g="g")
        logs = unify.get_logs()
        assert len(logs) == 2
        assert logs[1].entries == {"a": "a", "b": "b", "c": "c", "g": "g"}


@_handle_project
def test_global_logging():

    with unify.Log(a="a"):
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].entries == {"a": "a"}
        unify.log(b="b", c="c")
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].entries == {"a": "a", "b": "b", "c": "c"}
        with unify.Log(d="d"):
            logs = unify.get_logs()
            assert len(logs) == 2
            assert logs[0].entries == {"d": "d"}
            unify.log(e="e", f="f")
            logs = unify.get_logs()
            assert len(logs) == 2
            assert logs[0].entries == {"d": "d", "e": "e", "f": "f"}
        unify.log(g="g")
        logs = unify.get_logs()
        assert len(logs) == 2
        assert logs[1].entries == {"a": "a", "b": "b", "c": "c", "g": "g"}


@_handle_project
def test_with_log_threaded():
    def fn(a, b, c, d, e, f, g):
        with unify.Log(a=a):
            unify.add_log_entries(b=b, c=c)
            with unify.Log(d=d):
                unify.add_log_entries(e=e, f=f)
            unify.add_log_entries(g=g)

    threads = [
        threading.Thread(
            target=fn,
            args=[7 * i + j for j in range(7)],
        )
        for i in range(4)
    ]
    [t.start() for t in threads]
    [t.join() for t in threads]

    logs = unify.get_logs()
    entries = [log.entries for log in logs]

    assert sorted([sorted(d.items()) for d in entries]) == [
        [("a", i * 7), ("b", i * 7 + 1), ("c", i * 7 + 2), ("g", i * 7 + 6)]
        for i in range(4)
    ] + [[("d", i * 7 + 3), ("e", i * 7 + 4), ("f", i * 7 + 5)] for i in range(4)]


@_handle_project
@pytest.mark.asyncio
async def test_with_log_async():
    async def fn(a, b, c, d, e, f, g):
        with unify.Log(a=a):
            unify.add_log_entries(b=b, c=c)
            with unify.Log(d=d):
                unify.add_log_entries(e=e, f=f)
            unify.add_log_entries(g=g)

    fns = [fn(*[7 * i + j for j in range(7)]) for i in range(4)]
    await asyncio.gather(*fns)

    logs = unify.get_logs()
    entries = [log.entries for log in logs]

    assert sorted([sorted(d.items()) for d in entries]) == [
        [("a", i * 7), ("b", i * 7 + 1), ("c", i * 7 + 2), ("g", i * 7 + 6)]
        for i in range(4)
    ] + [[("d", i * 7 + 3), ("e", i * 7 + 4), ("f", i * 7 + 5)] for i in range(4)]


# Context


@_handle_project
def test_set_context():
    [unify.log(x=i) for i in range(3)]

    unify.set_context("Foo", mode="both")
    [unify.log(x=i) for i in range(10)]
    assert len(unify.get_logs()) == 10
    unify.unset_context()

    unify.set_context("Foo", mode="read")
    assert len(unify.get_logs()) == 10
    unify.unset_context()

    unify.set_context("Foo", mode="write")
    [unify.log(x=i) for i in range(10)]
    assert len(unify.get_logs()) == 3
    unify.unset_context()

    unify.set_context("Foo", mode="read")
    assert len(unify.get_logs()) == 20
    unify.unset_context()

    unify.set_context("Foo")
    assert len(unify.get_logs()) == 20
    unify.unset_context()


@_handle_project
def test_create_log_unique_column():
    unify.create_context(
        "foo",
        unique_keys={"unique_id": "int"},
        auto_counting={"unique_id": None},
    )
    ret = unify.log(context="foo")

    entries = ret.entries
    assert entries["unique_id"] is not None
    assert entries["unique_id"] == 0

    unify.delete_context("foo")
    unify.create_context("foo")
    ret = unify.log(context="foo")
    entries = ret.entries
    assert len(entries) == 0


@_handle_project
def test_create_log_unique_column_batch():
    unify.create_context(
        "foo",
        unique_keys={"unique_id": "int"},
        auto_counting={"unique_id": None},
    )
    ret = unify.create_logs(context="foo", entries=[{"x": 1}, {"x": 2}, {"x": 3}])

    for i, r in enumerate(ret):
        assert "unique_id" in r.entries
        assert r.entries["unique_id"] == i


@_handle_project
def test_create_logs_nested_ids():
    context_name = "foo_nested"
    unique_keys = {"run_id": "int", "step_id": "int"}
    auto_counting = {"run_id": None, "step_id": "run_id"}

    unify.create_context(
        context_name,
        unique_keys=unique_keys,
        auto_counting=auto_counting,
    )
    logs = unify.create_logs(context=context_name, entries=[{}])
    assert len(logs) == 1
    log = logs[0]
    assert log.entries["run_id"] == 0
    assert log.entries["step_id"] == 0

    batch_size = 3
    child_logs = unify.create_logs(
        context=context_name,
        entries=[{"data": f"step_{i}", "run_id": 0} for i in range(batch_size)],
    )
    assert len(child_logs) == batch_size
    for i, child_log in enumerate(child_logs):
        assert "run_id" in child_log.entries
        assert "step_id" in child_log.entries
        assert child_log.entries["run_id"] == 0
        assert child_log.entries["step_id"] == i + 1


@_handle_project
def test_log_auto_counting_independent_included_and_explicit_preserved():
    context_name = "independent_auto_count"
    unify.create_context(
        context_name,
        unique_keys={"run_id": "int"},
        auto_counting={
            "run_id": None,
            "ticket_id": None,
            "session_id": None,
        },
    )

    # First log: all counters auto-generate and initialize to 0
    lg1 = unify.log(context=context_name, action="init")
    e1 = lg1.entries
    assert e1["run_id"] == 0
    assert e1["ticket_id"] == 0
    assert e1["session_id"] == 0

    # Second log: explicit independent counters should be preserved
    lg2 = unify.log(
        context=context_name,
        ticket_id=999,
        session_id=888,
        action="explicit_independent_values",
    )
    e2 = lg2.entries
    assert e2["run_id"] == 1
    assert e2["ticket_id"] == 999
    assert e2["session_id"] == 888


@_handle_project
def test_create_logs_includes_independent_auto_counting_keys():
    ctx = "independent_auto_count_batch"
    unify.create_context(
        ctx,
        unique_keys={"dept": "int", "team": "int", "emp": "int"},
        auto_counting={
            "dept": None,
            "team": "dept",
            "emp": "team",
            "ticket_id": None,
            "session_id": None,
        },
    )

    # Initialize counters
    logs1 = unify.create_logs(context=ctx, entries=[{"action": "init_batch"}])
    assert len(logs1) == 1
    e1 = logs1[0].entries
    assert e1["dept"] == 0
    assert e1["team"] == 0
    assert e1["emp"] == 0
    assert e1["ticket_id"] == 0
    assert e1["session_id"] == 0

    # Next batch within same team should increment emp and independent counters
    logs2 = unify.create_logs(
        context=ctx,
        entries=[
            {"dept": 0, "team": 0, "action": "add_emp_1"},
            {"dept": 0, "team": 0, "action": "add_emp_2"},
        ],
    )
    assert len(logs2) == 2
    e2a = logs2[0].entries
    e2b = logs2[1].entries
    assert e2a["dept"] == 0 and e2a["team"] == 0
    assert e2b["dept"] == 0 and e2b["team"] == 0
    assert e2a["emp"] == 1
    assert e2b["emp"] == 2
    assert e2a["ticket_id"] == 1 and e2b["ticket_id"] == 2
    assert e2a["session_id"] == 1 and e2b["session_id"] == 2


@_handle_project
def test_create_logs_with_explicit_fields_and_payload_explicit_types():
    ctx = "explicit_fields_payload"

    # Ensure context exists
    unify.create_context(ctx)

    # Create explicit typed fields first
    fields = {
        "image_id": {"type": "int", "mutable": True},
        "timestamp": {"type": "datetime", "mutable": True},
        "caption": {"type": "str", "mutable": True},
        "data": {"type": "str", "mutable": True},
    }
    resp = unify.create_fields(fields=fields, context=ctx)
    assert isinstance(resp, dict)

    resp = unify.get_fields(context=ctx)
    assert resp["image_id"]["data_type"] == "int"
    assert resp["timestamp"]["data_type"] == "datetime"
    assert resp["caption"]["data_type"] == "str"
    assert resp["data"]["data_type"] == "str"

    # Provided payload with explicit types for 'data'
    payload = [
        {
            "timestamp": "2025-10-21T18:51:31.080494Z",
            "caption": "A small red square",
            "data": "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAAEUlEQVR42mP4z8CAFTEMLQkAKP8/wc53yE8AAAAASUVORK5CYII=",
            "explicit_types": {"data": {"type": "str"}},
        },
        {
            "timestamp": "2025-10-21T18:51:31.080500Z",
            "caption": "A tiny blue pixel",
            "data": "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAAEElEQVR42mNgYPiPAw0pCQCpcD/B/MtF/AAAAABJRU5ErkJggg==",
            "explicit_types": {"data": {"type": "str"}},
        },
    ]

    # Confirms the explicit type worked because the backend would otherwise infer the type of `data` as image
    created = unify.create_logs(context=ctx, entries=payload)
    assert len(created) == 2

    # Validate created entries and that explicit_types is not present in returned entries
    e0 = created[0].entries
    e1 = created[1].entries

    assert "explicit_types" not in e0
    assert "explicit_types" not in e1

    assert e0["caption"] == "A small red square"
    assert e1["caption"] == "A tiny blue pixel"

    assert (
        e0["data"]
        == "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAAEUlEQVR42mP4z8CAFTEMLQkAKP8/wc53yE8AAAAASUVORK5CYII="
    )
    assert (
        e1["data"]
        == "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAAEElEQVR42mNgYPiPAw0pCQCpcD/B/MtF/AAAAABJRU5ErkJggg=="
    )


if __name__ == "__main__":
    pass
