import uuid
from datetime import datetime

import unify

from .helpers import TEST_PROJECT, _handle_project, _handle_project_isolated


def _unique_context(base: str) -> str:
    """Generate unique context name for tests that manipulate context directly."""
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3]
    random_suffix = uuid.uuid4().hex[:4]
    return f"tests/test_logs/{base}/{timestamp}_{random_suffix}"


# =============================================================================
# Compositional log tests (set_context, Log class behavior, etc.)
# =============================================================================


def test_set_context():
    """Test context read/write mode behavior.

    This test manipulates context directly via set_context/unset_context,
    so it manages its own unique context rather than using @_handle_project.
    """
    # Ensure test project exists
    if TEST_PROJECT not in unify.list_projects():
        unify.create_project(TEST_PROJECT)
    unify.activate(TEST_PROJECT)

    # Create unique context paths for this test run
    root_ctx = _unique_context("test_set_context")
    foo_ctx = f"{root_ctx}/Foo"

    try:
        # Log to root context
        unify.set_context(root_ctx, relative=False)
        [unify.log(x=i) for i in range(3)]
        unify.unset_context()

        # Set both read and write to Foo
        unify.set_context(foo_ctx, mode="both", relative=False)
        [unify.log(x=i) for i in range(10)]
        assert len(unify.get_logs()) == 10
        unify.unset_context()

        # Set only read to Foo - should read 10 logs from Foo
        unify.set_context(foo_ctx, mode="read", relative=False)
        assert len(unify.get_logs()) == 10
        unify.unset_context()

        # Set only write to Foo, read from root - should read 3 logs from root
        unify.set_context(foo_ctx, mode="write", relative=False)
        unify.set_context(root_ctx, mode="read", relative=False)
        [unify.log(x=i) for i in range(10)]  # Writes to Foo
        assert len(unify.get_logs()) == 3  # Reads from root
        unify.unset_context()

        # Read from Foo should now have 20 logs
        unify.set_context(foo_ctx, mode="read", relative=False)
        assert len(unify.get_logs()) == 20
        unify.unset_context()

        # Both mode should also read 20
        unify.set_context(foo_ctx, relative=False)
        assert len(unify.get_logs()) == 20
        unify.unset_context()
    finally:
        unify.delete_context(root_ctx, delete_children=True)
        unify.unset_context()


@_handle_project_isolated
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


@_handle_project_isolated
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


@_handle_project_isolated
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


@_handle_project_isolated
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


@_handle_project_isolated
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


@_handle_project_isolated
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


@_handle_project_isolated
def test_create_logs_with_infer_untyped_fields():
    """Test that infer_untyped_fields causes untyped fields to get their types inferred.

    This test:
    1. Creates untyped fields (no explicit type provided)
    2. Verifies the fields have type "Any" initially
    3. Creates logs with infer_untyped_fields=True
    4. Verifies the fields' types are inferred from the data values
    5. Also confirms infer_untyped_fields is not in returned entries
    """
    ctx = "infer_untyped_fields_test"

    # Ensure context exists
    unify.create_context(ctx)

    # Create untyped fields (no explicit type)
    untyped_fields = ["score", "name", "count"]
    resp = unify.create_fields(fields=untyped_fields, context=ctx)
    assert isinstance(resp, dict)

    # Verify fields are untyped (type "Any")
    fields = unify.get_fields(context=ctx)
    assert fields["score"]["data_type"] == "Any"
    assert fields["name"]["data_type"] == "Any"
    assert fields["count"]["data_type"] == "Any"

    # Create logs with infer_untyped_fields=True
    # The backend should infer types based on the values
    payload = [
        {
            "score": 0.95,
            "name": "test_entry",
            "count": 42,
            "infer_untyped_fields": True,
        },
    ]
    created = unify.create_logs(context=ctx, entries=payload)
    assert len(created) == 1

    # Verify infer_untyped_fields is not present in returned entries
    e0 = created[0].entries
    assert "infer_untyped_fields" not in e0
    assert e0["score"] == 0.95
    assert e0["name"] == "test_entry"
    assert e0["count"] == 42

    # Verify the fields now have inferred types
    fields_after = unify.get_fields(context=ctx)
    assert fields_after["score"]["data_type"] == "float"
    assert fields_after["name"]["data_type"] == "str"
    assert fields_after["count"]["data_type"] == "int"


@_handle_project_isolated
def test_log_with_infer_untyped_fields():
    """Test infer_untyped_fields works with the single log() function as well."""
    ctx = "infer_untyped_single_log"

    # Ensure context exists
    unify.create_context(ctx)

    # Create untyped fields
    untyped_fields = ["value", "label"]
    unify.create_fields(fields=untyped_fields, context=ctx)

    # Verify fields are untyped
    fields = unify.get_fields(context=ctx)
    assert fields["value"]["data_type"] == "Any"
    assert fields["label"]["data_type"] == "Any"

    # Log with infer_untyped_fields=True
    lg = unify.log(
        context=ctx,
        value=123.45,
        label="some_label",
        infer_untyped_fields=True,
    )

    # Verify infer_untyped_fields is not in entries
    assert "infer_untyped_fields" not in lg.entries
    assert lg.entries["value"] == 123.45
    assert lg.entries["label"] == "some_label"

    # Verify fields now have inferred types
    fields_after = unify.get_fields(context=ctx)
    assert fields_after["value"]["data_type"] == "float"
    assert fields_after["label"]["data_type"] == "str"


@_handle_project_isolated
def test_infer_untyped_fields_defaults_to_false():
    """Test that without infer_untyped_fields, fields remain untyped.

    This confirms the default behavior (infer_untyped_fields=False) where
    untyped fields stay as "Any" even after logging data.
    """
    ctx = "infer_untyped_default_false"

    # Ensure context exists
    unify.create_context(ctx)

    # Create untyped fields
    untyped_fields = ["metric"]
    unify.create_fields(fields=untyped_fields, context=ctx)

    # Verify field is untyped
    fields = unify.get_fields(context=ctx)
    assert fields["metric"]["data_type"] == "Any"

    # Log WITHOUT infer_untyped_fields (defaults to False)
    lg = unify.log(context=ctx, metric=99.9)
    assert lg.entries["metric"] == 99.9

    # Field should still be untyped
    fields_after = unify.get_fields(context=ctx)
    assert fields_after["metric"]["data_type"] == "Any"


# =============================================================================
# Core log API tests (CRUD, filtering, metrics, etc.)
# =============================================================================


@_handle_project
def test_create_logs():
    entries = [
        {"a": 0, "b": 1, "c": 2},
        {"a": 1, "b": 2, "c": 3},
        {"a": 2, "b": 3, "c": 4},
    ]
    unify.create_logs(entries=entries, batched=False)
    logs_unbatched = unify.get_logs()
    assert len(logs_unbatched) == 3
    unify.delete_logs()
    unify.create_logs(entries=entries, batched=True)
    logs_batched = unify.get_logs()
    assert len(logs_batched) == 3


@_handle_project
def test_create_logs_large_body():
    entries = [{"img": "a" * 100000}] * 100
    unify.create_logs(entries=entries)
    assert len(unify.get_logs()) == 100


@_handle_project_isolated
def test_update_logs():
    log0 = unify.log(a=0, b=1)
    unify.update_logs(logs=log0, entries={"a": 1}, overwrite=True)
    assert unify.get_logs(from_ids=[log0.id])[0].entries["a"] == 1
    unify.update_logs(logs=log0, entries={"c": 2})
    assert unify.get_logs(from_ids=[log0.id])[0].entries["c"] == 2
    log1 = unify.log(a=1, b=2)
    unify.update_logs(logs=[log0, log1], entries=[{"a": 3}, {"a": 4}], overwrite=True)
    assert unify.get_logs(from_ids=[log0.id])[0].entries["a"] == 3
    assert unify.get_logs(from_ids=[log1.id])[0].entries["a"] == 4


@_handle_project
def test_log_function_logs_code():
    def my_func(a):
        return a + 1

    unify.log(my_func=my_func)
    logs = unify.get_logs()
    assert len(logs) == 1
    assert logs[0].entries["my_func"] == "    def my_func(a):\n        return a + 1\n"


@_handle_project
def test_atomic_functions():
    log1 = {
        "system_prompt": "You are a weather assistant",
        "user_prompt": "hello world",
        "score": 0.2,
    }
    log2 = {
        "system_prompt": "You are a new weather assistant",
        "user_prompt": "hello world",
        "score": 0.3,
    }
    log3 = {
        "system_prompt": "You are a new weather assistant",
        "user_prompt": "nothing",
        "score": 0.8,
    }
    unify.log(**log1)
    unify.log(**log2)
    unify.log(**log3)

    logs_metric = unify.get_logs_metric(
        metric="mean",
        key="score",
        filter="'hello' in user_prompt",
    )
    assert logs_metric == 0.25


@_handle_project
def test_get_logs_metric_multiple_keys():
    """Test get_logs_metric with multiple keys (no grouping)."""
    log1 = {"score": 0.2, "length": 10}
    log2 = {"score": 0.3, "length": 20}
    log3 = {"score": 0.8, "length": 30}
    unify.log(**log1)
    unify.log(**log2)
    unify.log(**log3)

    # Test multiple keys - should return a dict
    result = unify.get_logs_metric(
        metric="mean",
        key=["score", "length"],
    )
    assert isinstance(result, dict), "Multiple keys should return a dict"
    assert "score" in result
    assert "length" in result
    assert abs(result["score"] - 0.433333) < 0.01  # (0.2 + 0.3 + 0.8) / 3
    assert result["length"] == 20.0  # (10 + 20 + 30) / 3


@_handle_project
def test_get_logs_metric_with_grouping():
    """Test get_logs_metric with single-level grouping."""
    # Create logs with different categories
    unify.log(score=0.2, category="A")
    unify.log(score=0.3, category="A")
    unify.log(score=0.8, category="B")
    unify.log(score=0.9, category="B")

    # Test single-level grouping
    result = unify.get_logs_metric(
        metric="mean",
        key="score",
        group_by="category",
    )
    assert isinstance(result, dict), "Grouped result should be a dict"
    assert "A" in result
    assert "B" in result
    # Mean for category A: (0.2 + 0.3) / 2 = 0.25
    assert abs(result["A"].get("mean", result["A"].get("shared_value")) - 0.25) < 0.01
    # Mean for category B: (0.8 + 0.9) / 2 = 0.85
    assert abs(result["B"].get("mean", result["B"].get("shared_value")) - 0.85) < 0.01


@_handle_project
def test_get_logs_metric_with_nested_grouping():
    """Test get_logs_metric with nested grouping."""
    # Create logs with different categories and subcategories
    unify.log(score=0.2, category="A", subcategory="X")
    unify.log(score=0.3, category="A", subcategory="Y")
    unify.log(score=0.8, category="B", subcategory="X")
    unify.log(score=0.9, category="B", subcategory="Y")

    # Test nested grouping
    result = unify.get_logs_metric(
        metric="mean",
        key="score",
        group_by=["category", "subcategory"],
    )
    assert isinstance(result, dict), "Nested grouped result should be a dict"
    assert "A" in result
    assert "B" in result
    assert isinstance(result["A"], dict), "First level should be a dict"
    assert isinstance(result["B"], dict), "First level should be a dict"
    assert "X" in result["A"]
    assert "Y" in result["A"]
    assert "X" in result["B"]
    assert "Y" in result["B"]


@_handle_project
def test_get_logs_metric_multiple_keys_with_grouping():
    """Test get_logs_metric with multiple keys and grouping."""
    unify.log(score=0.2, length=10, category="A")
    unify.log(score=0.3, length=20, category="A")
    unify.log(score=0.8, length=30, category="B")
    unify.log(score=0.9, length=40, category="B")

    # Test multiple keys with grouping
    result = unify.get_logs_metric(
        metric="mean",
        key=["score", "length"],
        group_by="category",
    )
    assert isinstance(result, dict), "Result should be a dict"
    assert "score" in result
    assert "length" in result
    assert isinstance(result["score"], dict), "Score results should be grouped"
    assert isinstance(result["length"], dict), "Length results should be grouped"
    assert "A" in result["score"]
    assert "B" in result["score"]
    assert "A" in result["length"]
    assert "B" in result["length"]


@_handle_project
def test_get_logs_metric_key_specific_filters():
    """Test get_logs_metric with key-specific filter expressions."""
    unify.log(score=0.2, length=10)
    unify.log(score=0.3, length=20)
    unify.log(score=0.8, length=30)

    # Test key-specific filters
    result = unify.get_logs_metric(
        metric="mean",
        key=["score", "length"],
        filter={"score": "score > 0.25", "length": "length > 15"},
    )
    assert isinstance(result, dict), "Result should be a dict"
    assert "score" in result
    assert "length" in result
    # Score filter: only logs with score > 0.25 (0.3 and 0.8), mean = 0.55
    assert abs(result["score"] - 0.55) < 0.01
    # Length filter: only logs with length > 15 (20 and 30), mean = 25.0
    assert result["length"] == 25.0


@_handle_project
def test_get_logs_metric_key_specific_from_ids():
    """Test get_logs_metric with key-specific from_ids."""
    log1 = unify.log(score=0.2, length=10)
    log2 = unify.log(score=0.3, length=20)
    log3 = unify.log(score=0.8, length=30)

    # Test key-specific from_ids
    result = unify.get_logs_metric(
        metric="mean",
        key=["score", "length"],
        from_ids={"score": f"{log1.id}&{log2.id}", "length": f"{log2.id}&{log3.id}"},
    )
    assert isinstance(result, dict), "Result should be a dict"
    assert "score" in result
    assert "length" in result
    # Score from_ids: logs 1 and 2, mean = (0.2 + 0.3) / 2 = 0.25
    assert abs(result["score"] - 0.25) < 0.01
    # Length from_ids: logs 2 and 3, mean = (20 + 30) / 2 = 25.0
    assert result["length"] == 25.0


@_handle_project
def test_get_logs_metric_key_specific_exclude_ids():
    """Test get_logs_metric with key-specific exclude_ids."""
    log1 = unify.log(score=0.2, length=10)
    log2 = unify.log(score=0.3, length=20)
    log3 = unify.log(score=0.8, length=30)

    # Test key-specific exclude_ids
    result = unify.get_logs_metric(
        metric="mean",
        key=["score", "length"],
        exclude_ids={"score": f"{log3.id}", "length": f"{log1.id}"},
    )
    assert isinstance(result, dict), "Result should be a dict"
    assert "score" in result
    assert "length" in result
    # Score exclude_ids: exclude log3, mean of logs 1 and 2 = (0.2 + 0.3) / 2 = 0.25
    assert abs(result["score"] - 0.25) < 0.01
    # Length exclude_ids: exclude log1, mean of logs 2 and 3 = (20 + 30) / 2 = 25.0
    assert result["length"] == 25.0


@_handle_project
def test_get_logs_metric_backward_compatibility():
    """Test that the existing single-key API still works (backward compatibility)."""
    unify.log(score=0.2)
    unify.log(score=0.3)
    unify.log(score=0.8)

    # Test legacy single-key format - should return scalar
    result = unify.get_logs_metric(
        metric="mean",
        key="score",
    )
    assert isinstance(result, (int, float)), "Single key should return scalar"
    assert abs(result - 0.433333) < 0.01  # (0.2 + 0.3 + 0.8) / 3

    # Test legacy filter format
    result = unify.get_logs_metric(
        metric="mean",
        key="score",
        filter="score > 0.25",
    )
    assert isinstance(
        result,
        (int, float),
    ), "Single key with filter should return scalar"
    assert abs(result - 0.55) < 0.01  # (0.3 + 0.8) / 2

    # Test legacy from_ids format
    logs = [unify.log(score=i * 0.1) for i in range(5)]
    result = unify.get_logs_metric(
        metric="mean",
        key="score",
        from_ids=[logs[0].id, logs[1].id, logs[2].id],
    )
    assert isinstance(
        result,
        (int, float),
    ), "Single key with from_ids should return scalar"
    assert abs(result - 0.1) < 0.01  # (0.0 + 0.1 + 0.2) / 3


@_handle_project
def test_log_ordering():
    for i in range(25):
        unify.log(
            a=i,
            b=i + 1,
            c=i + 2,
        )
    logs = unify.get_logs()
    for lg in logs:
        assert list(lg.entries.keys()) == ["a", "b", "c"]


@_handle_project
def test_get_logs():
    logs = unify.get_logs()
    assert len(logs) == 0, "There should be no logs initially."
    log_data1 = {
        "system_prompt": "You are a weather assistant",
        "user_prompt": "What is the weather today?",
        "score": 0.9,
    }
    unify.log(**log_data1)
    log_data2 = {
        "system_prompt": "You are a travel assistant",
        "user_prompt": "What is the best route to the airport?",
        "score": 0.7,
    }
    unify.log(**log_data2)
    log_data3 = {
        "system_prompt": "You are a travel assistant",
        "user_prompt": "What is the best route to the airport?",
        "score": 0.2,
    }
    unify.log(**log_data3)

    logs = unify.get_logs()
    assert len(logs) == 3, "There should be 3 logs in the project."
    filtered_logs = unify.get_logs(
        filter="'weather' in user_prompt",
    )
    assert (
        len(filtered_logs) == 1
    ), "There should be 1 log with 'weather' in the user prompt."
    assert (
        filtered_logs[0].entries.get("user_prompt") == log_data1["user_prompt"]
    ), "The filtered log should be the one that asks about the weather."
    nonexistent_logs = unify.get_logs(
        filter="'nonexistent' in user_prompt",
    )
    assert (
        len(nonexistent_logs) == 0
    ), "There should be no logs matching the nonexistent filter."
    multiple_filtered_logs = unify.get_logs(
        filter="'travel' in system_prompt and score < 0.5",
    )
    assert (
        len(multiple_filtered_logs) == 1
    ), "There should be 1 log with 'travel' in the user prompt and score > 0.5."
    bracket_logs = unify.get_logs(
        filter="('weather' in user_prompt) and ('weather' in system_prompt)",
    )
    assert (
        len(bracket_logs) == 1
    ), "There should be 1 log with 'weather' in the user prompt and system prompt."
    assert (
        bracket_logs[0].entries.get("user_prompt") == log_data1["user_prompt"]
    ), "The filtered log should be the one that asks about the weather."
    comparison_logs = unify.get_logs(filter="score > 0.5")
    assert len(comparison_logs) == 2, "There should be 2 logs with score > 0.5."
    comparison_logs = unify.get_logs(filter="score == 0.9")
    assert len(comparison_logs) == 1, "There should be 1 log with score == 0.9."
    logical_logs = unify.get_logs(
        filter="score > 0.5 and score < 0.8",
    )
    assert (
        len(logical_logs) == 1
    ), "There should be 1 log with score > 0.5 and score < 0.8."
    logical_logs = unify.get_logs(
        filter="score < 0.5 or score > 0.8",
    )
    assert (
        len(logical_logs) == 2
    ), "There should be 2 logs with score < 0.5 or score > 0.8."
    string_comparison_logs = unify.get_logs(
        filter="user_prompt == 'What is the weather today?'",
    )
    assert (
        len(string_comparison_logs) == 1
    ), "There should be 1 log with user_prompt == 'What is the weather today?'."


@_handle_project
def test_get_logs_from_ids():
    logs = [unify.log(x=i) for i in range(5)]
    ids = [l.id for l in logs]

    logs_from_ids = unify.get_logs(from_ids=[ids[0]])
    assert len(logs_from_ids) == 1
    assert logs_from_ids[0].id == ids[0]

    logs_from_ids = unify.get_logs(from_ids=ids)
    assert len(logs_from_ids) == 5
    for l in logs_from_ids:
        assert l.id in ids

    logs_from_ids = unify.get_logs(from_ids=ids[0:2])
    assert len(logs_from_ids) == 2
    for l in logs_from_ids:
        assert l.id in ids[0:2]


@_handle_project
def test_get_logs_from_fields():
    [unify.log(x=i) for i in range(3)]
    logs = unify.get_logs(from_fields=["x"])
    assert len(logs) == 3

    [unify.log(y=i) for i in range(3)]
    logs = unify.get_logs(from_fields=["y"])
    assert len(logs) == 3

    logs = unify.get_logs(from_fields=["x", "y"])
    assert len(logs) == 6


@_handle_project
def test_get_logs_exclude_fields():
    [unify.log(x=i) for i in range(3)]
    assert len(unify.get_logs()) == 3

    logs = unify.get_logs(exclude_fields=["x"])
    assert len(logs) == 0

    [unify.log(y=i) for i in range(3)]
    logs = unify.get_logs(exclude_fields=["x"])
    assert len(logs) == 3

    logs = unify.get_logs(exclude_fields=["x", "y"])
    assert len(logs) == 0


@_handle_project
def test_get_logs_exclude_ids():
    logs = [unify.log(x=i) for i in range(5)]
    ids = [l.id for l in logs]

    logs_exclude_ids = unify.get_logs(exclude_ids=[ids[0]])
    assert len(logs_exclude_ids) == 4
    for l in logs_exclude_ids:
        assert l.id != ids[0]

    logs_exclude_ids = unify.get_logs(exclude_ids=ids)
    assert len(logs_exclude_ids) == 0

    logs_exclude_ids = unify.get_logs(exclude_ids=ids[0:2])
    assert len(logs_exclude_ids) == 3


@_handle_project
def test_get_logs_value_limit():
    msg = "hello world"
    unify.log(msg=msg)
    logs = unify.get_logs(value_limit=5)
    assert len(logs) == 1
    assert logs[0].entries["msg"] == msg[:5] + "..."

    logs = unify.get_logs(value_limit=None)
    assert logs[0].entries["msg"] == msg


@_handle_project
def test_get_logs_group_by():
    for i in range(2):
        for y in range(3):
            unify.log(x=i, y=y)

    logs = unify.get_logs(group_by=["x"])
    assert isinstance(logs, unify.LogGroup)
    assert logs.field == "x"
    assert len(logs.value) == 2
    assert "0" in logs.value
    assert "1" in logs.value
    assert len(logs.value["0"]) == 3
    assert len(logs.value["1"]) == 3

    logs = unify.get_logs(group_by=["y"])
    assert isinstance(logs, unify.LogGroup)
    assert logs.field == "y"
    assert len(logs.value) == 3


@_handle_project
def test_get_logs_group_by_entries():
    unify.log(name="John", age=21, msg="Hello")
    unify.log(name="John", age=21, msg="Bye")

    logs = unify.get_logs(group_by=["name", "msg"])
    assert isinstance(logs, unify.LogGroup)
    assert logs.field == "name"
    assert "John" in logs.value

    second_group = logs.value["John"]
    assert isinstance(second_group, unify.LogGroup)
    assert second_group.field == "msg"
    assert "Hello" in second_group.value
    assert "Bye" in second_group.value

    log = logs.value["John"].value["Hello"][0]
    assert log.entries["name"] == "John"
    assert log.entries["msg"] == "Hello"

    log = logs.value["John"].value["Bye"][0]
    assert log.entries["name"] == "John"
    assert log.entries["msg"] == "Bye"


@_handle_project
def test_get_logs_group_by_not_nested():
    for i in range(2):
        for y in range(3):
            unify.log(x=i, y=y)

    logs = unify.get_logs(group_by=["x"], nested_groups=False)
    assert isinstance(logs, list)
    assert len(logs) == 1
    for _, v in logs[0].value.items():
        assert isinstance(v, list)
        for log in v:
            assert isinstance(log, unify.Log)


@_handle_project
def test_delete_logs_by_ids():
    logs = [unify.log(x=i) for i in range(3)]
    assert len(unify.get_logs()) == 3

    deleted_id = logs[0].id
    unify.delete_logs(logs=logs[0])
    logs = unify.get_logs()
    assert len(logs) == 2
    assert all(log.id != deleted_id for log in logs)

    unify.delete_logs(logs=logs)
    assert len(unify.get_logs()) == 0


@_handle_project
def test_create_fields():
    field_name = "full_name"
    unify.create_fields(fields={field_name: "str"})
    fields = unify.get_fields()
    assert field_name in fields
    assert fields[field_name]["data_type"] == "str"


@_handle_project
def test_rename_field():
    field_name = "full_name"
    unify.log(**{field_name: "John Doe"})
    fields = unify.get_fields()
    assert field_name in fields

    new_field_name = "name"
    unify.rename_field(name=field_name, new_name=new_field_name)

    fields = unify.get_fields()
    assert new_field_name in fields
    assert field_name not in fields

    logs = unify.get_logs()
    assert len(logs) == 1
    assert logs[0].entries[new_field_name] == "John Doe"


@_handle_project
def test_get_fields():
    assert len(unify.get_fields()) == 0

    field_name = "full_name"
    unify.create_fields(fields={field_name: None})
    fields = unify.get_fields()
    assert field_name in fields


@_handle_project
def test_delete_fields():
    field_name = "full_name"
    other_field = "age"
    unify.log(**{field_name: "John", other_field: 30})
    fields = unify.get_fields()
    assert field_name in fields
    assert other_field in fields
    assert len(unify.get_logs()) == 1

    unify.delete_fields([field_name])

    # Deleting fields removes the field data, but preserves the log
    logs = unify.get_logs()
    assert len(logs) == 1
    assert field_name not in logs[0].entries
    assert other_field in logs[0].entries
    assert logs[0].entries[other_field] == 30

    fields = unify.get_fields()
    assert field_name not in fields
    assert other_field in fields


@_handle_project
def test_atomic_update_increment():
    """Test atomic increment operation."""
    log = unify.log(counter=10)
    new_value = unify.atomic_update(log, "counter", "+5")
    assert new_value == 15.0


@_handle_project
def test_atomic_update_decrement():
    """Test atomic decrement operation."""
    log = unify.log(counter=100)
    new_value = unify.atomic_update(log.id, "counter", "-30")
    assert new_value == 70.0


@_handle_project
def test_atomic_update_multiply():
    """Test atomic multiplication operation."""
    log = unify.log(value=7)
    new_value = unify.atomic_update(log, "value", "*3")
    assert new_value == 21.0


@_handle_project
def test_atomic_update_divide():
    """Test atomic division operation."""
    log = unify.log(value=100)
    new_value = unify.atomic_update(log, "value", "/4")
    assert new_value == 25.0


@_handle_project
def test_atomic_update_on_null_key():
    """Test atomic operation on a key that doesn't exist (should treat as 0)."""
    log = unify.log(other_key="value")
    new_value = unify.atomic_update(log, "counter", "+5")
    assert new_value == 5.0


@_handle_project
def test_atomic_update_with_float_operand():
    """Test atomic operation with decimal operand."""
    log = unify.log(score=10)
    new_value = unify.atomic_update(log, "score", "*1.5")
    assert new_value == 15.0


@_handle_project
def test_atomic_update_sequential():
    """Test multiple sequential atomic operations on the same key."""
    log = unify.log(value=10)

    # 10 + 5 = 15
    new_value = unify.atomic_update(log, "value", "+5")
    assert new_value == 15.0

    # 15 * 2 = 30
    new_value = unify.atomic_update(log, "value", "*2")
    assert new_value == 30.0

    # 30 - 10 = 20
    new_value = unify.atomic_update(log, "value", "-10")
    assert new_value == 20.0

    # 20 / 4 = 5
    new_value = unify.atomic_update(log, "value", "/4")
    assert new_value == 5.0


@_handle_project_isolated
def test_create_logs_recompute_derived():
    """Verify that recompute_derived triggers inline derived column computation."""
    ctx = _unique_context("recompute_derived")
    try:
        unify.create_context(ctx)

        # Seed a log so the derived template has something to reference
        seed = unify.create_logs(context=ctx, entries=[{"base_value": 1}])

        # Create a derived template (filter_expr to get an ActiveDerivedLog)
        unify.create_derived_logs(
            key="derived_value",
            equation="{log:base_value} * 10",
            referenced_logs={"log": {"context": ctx}},
            context=ctx,
        )

        # Create with recompute_derived=True — derived value should be present
        logs_with = unify.create_logs(
            context=ctx,
            entries=[{"base_value": 5}],
            recompute_derived=True,
        )
        fetched = unify.get_logs(context=ctx, from_ids=[logs_with[0].id])
        assert len(fetched) == 1
        derived = getattr(fetched[0], "entries", {}) or {}
        assert (
            derived.get("derived_value") == 50
        ), f"Expected 50, got {derived.get('derived_value')}"

        # Create without recompute_derived — derived value should be absent
        logs_without = unify.create_logs(
            context=ctx,
            entries=[{"base_value": 7}],
        )
        fetched = unify.get_logs(context=ctx, from_ids=[logs_without[0].id])
        assert len(fetched) == 1
        derived = getattr(fetched[0], "entries", {}) or {}
        assert derived.get("derived_value") is None
    finally:
        unify.delete_context(ctx)


@_handle_project_isolated
def test_create_logs_partial_failure_correct_alignment():
    """When some entries fail type enforcement, returned Logs must align with the
    correct entries (not shifted) and len(result) must equal the successful count."""
    ctx = _unique_context("partial_failure_alignment")
    try:
        unify.create_context(ctx)

        # Pre-create strict typed fields so type-mismatched entries will be rejected
        unify.create_fields(
            {
                "age": {"type": "int", "mutable": True},
                "name": {"type": "str", "mutable": True},
            },
            context=ctx,
        )

        entries = [
            {"name": "ok-1", "age": 10},
            {"name": "bad", "age": "not_an_int"},  # will fail type enforcement
            {"name": "ok-2", "age": 20},
            {"name": "also-bad", "age": "nope"},  # will also fail
            {"name": "ok-3", "age": 30},
        ]

        result = unify.create_logs(context=ctx, entries=entries)

        # Only 3 of 5 entries should succeed
        assert len(result) == 3, f"Expected 3 logs, got {len(result)}"

        # Verify alignment: each Log should have the correct name/age pair
        result_names = sorted(log.entries.get("name") for log in result)
        assert result_names == ["ok-1", "ok-2", "ok-3"], f"Got {result_names}"

        # Verify server-side: only 3 logs exist
        server_logs = unify.get_logs(context=ctx)
        assert len(server_logs) == 3
        server_names = sorted(log.entries.get("name") for log in server_logs)
        assert server_names == ["ok-1", "ok-2", "ok-3"]
    finally:
        unify.delete_context(ctx)


@_handle_project_isolated
def test_create_logs_partial_failure_warning():
    """create_logs emits a warning when entries fail."""
    import warnings as _warnings

    ctx = _unique_context("partial_failure_warning")
    try:
        unify.create_context(ctx)

        unify.create_fields(
            {"val": {"type": "int", "mutable": True}},
            context=ctx,
        )

        entries = [
            {"val": 1},
            {"val": "not_int"},  # will fail
            {"val": 3},
        ]

        with _warnings.catch_warnings(record=True) as w:
            _warnings.simplefilter("always")
            result = unify.create_logs(context=ctx, entries=entries)

        assert len(result) == 2

        warning_msgs = [str(x.message) for x in w]
        assert any(
            "1 of 3 entries failed" in m for m in warning_msgs
        ), f"Expected partial failure warning, got: {warning_msgs}"
    finally:
        unify.delete_context(ctx)


@_handle_project_isolated
def test_join_query_reduce():
    """Fused join_query in reduce mode returns aggregated results."""
    ctx_a = "orders"
    ctx_b = "users"
    unify.create_context(ctx_a)
    unify.create_context(ctx_b)

    unify.create_logs(
        entries=[
            {"user_id": 1, "amount": 10},
            {"user_id": 2, "amount": 20},
            {"user_id": 1, "amount": 30},
        ],
        context=ctx_a,
    )
    unify.create_logs(
        entries=[
            {"user_id": 1, "name": "Alice"},
            {"user_id": 2, "name": "Bob"},
        ],
        context=ctx_b,
    )

    result = unify.join_query(
        pair_of_args=({"context": ctx_a}, {"context": ctx_b}),
        join_expr="A.user_id == B.user_id",
        mode="inner",
        columns={"A.user_id": "user_id", "A.amount": "amount", "B.name": "name"},
        metric="sum",
        key="amount",
    )
    assert result == 60  # 10 + 30 + 20


@_handle_project_isolated
def test_join_query_rows():
    """Fused join_query in row mode returns paginated rows."""
    ctx_a = "orders"
    ctx_b = "users"
    unify.create_context(ctx_a)
    unify.create_context(ctx_b)

    unify.create_logs(
        entries=[
            {"user_id": 1, "amount": 10},
            {"user_id": 2, "amount": 20},
        ],
        context=ctx_a,
    )
    unify.create_logs(
        entries=[
            {"user_id": 1, "name": "Alice"},
            {"user_id": 2, "name": "Bob"},
        ],
        context=ctx_b,
    )

    result = unify.join_query(
        pair_of_args=({"context": ctx_a}, {"context": ctx_b}),
        join_expr="A.user_id == B.user_id",
        mode="inner",
        columns={"A.user_id": "user_id", "A.amount": "amount", "B.name": "name"},
    )
    assert "logs" in result
    assert "count" in result
    assert result["count"] == 2
    assert len(result["logs"]) == 2


@_handle_project_isolated
def test_join_query_matches_legacy():
    """Fused join_query reduce result matches legacy join+metric+delete."""
    ctx_a = "orders"
    ctx_b = "users"
    unify.create_context(ctx_a)
    unify.create_context(ctx_b)

    unify.create_logs(
        entries=[
            {"user_id": 1, "amount": 10},
            {"user_id": 2, "amount": 20},
            {"user_id": 1, "amount": 30},
        ],
        context=ctx_a,
    )
    unify.create_logs(
        entries=[
            {"user_id": 1, "name": "Alice"},
            {"user_id": 2, "name": "Bob"},
        ],
        context=ctx_b,
    )

    columns = {"A.user_id": "user_id", "A.amount": "amount", "B.name": "name"}

    # Legacy path
    unify.join_logs(
        pair_of_args=({"context": ctx_a}, {"context": ctx_b}),
        join_expr="A.user_id == B.user_id",
        mode="inner",
        new_context="_legacy_temp",
        columns=list(columns.keys()),
    )
    legacy_result = unify.get_logs_metric(
        key="amount",
        metric="sum",
        context="_legacy_temp",
    )
    unify.delete_context("_legacy_temp")

    # Fused path
    fused_result = unify.join_query(
        pair_of_args=({"context": ctx_a}, {"context": ctx_b}),
        join_expr="A.user_id == B.user_id",
        mode="inner",
        columns=columns,
        metric="sum",
        key="amount",
    )

    legacy_val = (
        legacy_result
        if isinstance(legacy_result, (int, float))
        else legacy_result.get("sum", legacy_result)
    )
    assert float(fused_result) == float(legacy_val)


# ---------------------------------------------------------------------------
# join_query validation rejection tests
# ---------------------------------------------------------------------------

_JQ_BASE = dict(
    pair_of_args=({"context": "a"}, {"context": "b"}),
    join_expr="A.x == B.x",
    mode="inner",
)


@_handle_project_isolated
def test_join_query_key_without_metric_400():
    """Server rejects key without metric with 400."""
    unify.create_context("a")
    unify.create_context("b")
    unify.create_logs(entries=[{"x": 1, "v": 10}], context="a")
    unify.create_logs(entries=[{"x": 1, "v": 20}], context="b")

    import pytest

    with pytest.raises(unify.RequestError) as exc_info:
        unify.join_query(**_JQ_BASE, key="v")
    assert (
        exc_info.value.response.status_code == 400
        or "key" in str(exc_info.value).lower()
    )


@_handle_project_isolated
def test_join_query_group_by_without_metric_400():
    """Server rejects group_by without metric with 400."""
    unify.create_context("a")
    unify.create_context("b")
    unify.create_logs(entries=[{"x": 1, "v": 10}], context="a")
    unify.create_logs(entries=[{"x": 1, "v": 20}], context="b")

    import pytest

    with pytest.raises(unify.RequestError) as exc_info:
        unify.join_query(**_JQ_BASE, group_by="x")
    assert (
        exc_info.value.response.status_code == 400
        or "group_by" in str(exc_info.value).lower()
    )


@_handle_project_isolated
def test_join_query_sorting_in_reduce_400():
    """Server rejects sorting when metric is set with 400."""
    unify.create_context("a")
    unify.create_context("b")
    unify.create_logs(entries=[{"x": 1, "v": 10}], context="a")
    unify.create_logs(entries=[{"x": 1, "v": 20}], context="b")

    import pytest

    with pytest.raises(unify.RequestError) as exc_info:
        unify.join_query(
            **_JQ_BASE,
            metric="sum",
            key="v",
            sorting='{"v": "ascending"}',
        )
    assert (
        exc_info.value.response.status_code == 400
        or "sorting" in str(exc_info.value).lower()
    )


if __name__ == "__main__":
    pass
