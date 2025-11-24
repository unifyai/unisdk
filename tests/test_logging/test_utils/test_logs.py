import pytest
import unify

from ..helpers import _handle_project


@_handle_project
def test_log_entry():
    data = {
        "question": "What is 1 + 1?",
        "answer": "It's 2",
    }
    assert len(unify.get_logs()) == 0
    log_id = unify.log(**data).id
    project_logs = unify.get_logs()
    assert len(project_logs) and project_logs[0].id == log_id
    id_log = unify.get_log_by_id(log_id)
    assert len(id_log) and "question" in id_log.entries
    unify.delete_log_fields(field="question", logs=log_id)
    id_log = unify.get_log_by_id(log_id)
    assert len(id_log) and "question" not in id_log.entries
    unify.add_log_entries(logs=log_id, question=data["question"])
    id_log = unify.get_log_by_id(log_id)
    assert len(id_log) and "question" in id_log.entries
    unify.delete_logs(logs=log_id)
    assert len(unify.get_logs()) == 0
    try:
        unify.get_log_by_id(log_id)
        assert False
    except Exception as e:
        assert str(e) == f"Log with id {log_id} does not exist"


@_handle_project
def test_create_logs():
    entries = [
        {"a": 0, "b": 1, "c": 2},
        {"a": 1, "b": 2, "c": 3},
        {"a": 2, "b": 3, "c": 4},
    ]
    params = [
        {"x": -1, "y": -2, "z": -3},
        {"x": -4, "y": -5, "z": -6},
        {"x": -7, "y": -8, "z": -9},
    ]
    unify.create_logs(entries=entries, params=params, batched=False)
    logs_unbatched = unify.get_logs()
    assert len(logs_unbatched) == 3
    unify.delete_logs()
    unify.create_logs(entries=entries, params=params, batched=True)
    logs_batched = unify.get_logs()
    assert len(logs_batched) == 3


@_handle_project
def test_create_logs_large_body():
    entries = [{"img": "a" * 100000}] * 100
    unify.create_logs(entries=entries)
    assert len(unify.get_logs()) == 100


@_handle_project
def test_update_logs():
    log0 = unify.log(a=0, b=1)
    unify.update_logs(logs=log0, entries={"a": 1}, overwrite=True)
    assert unify.get_log_by_id(log0.id).entries["a"] == 1
    unify.update_logs(logs=log0, entries={"c": 2})
    assert unify.get_log_by_id(log0.id).entries["c"] == 2
    log1 = unify.log(a=1, b=2)
    unify.update_logs(logs=[log0, log1], entries=[{"a": 3}, {"a": 4}], overwrite=True)
    assert unify.get_log_by_id(log0.id).entries["a"] == 3
    assert unify.get_log_by_id(log1.id).entries["a"] == 4


@_handle_project
def test_duplicate_log_field():
    data = {
        "system_prompt": "You are a weather assistant",
        "user_prompt": "hello world",
    }
    assert len(unify.get_logs()) == 0
    log = unify.log(**data)
    assert len(unify.get_logs()) == 1
    new_data = {
        "system_prompt": "You are a maths assistant",
        "user_prompt": "hi earth",
    }
    with pytest.raises(Exception):
        log.add_entries(**new_data)


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
def test_get_source():
    source = unify.get_source()
    assert "source = unify.get_source()" in source


@_handle_project
def test_delete_logs_by_ids():
    logs = [unify.log(x=i) for i in range(3)]
    assert len(unify.get_logs()) == 3

    unify.delete_logs(logs=logs[0])
    logs = unify.get_logs()
    assert len(logs) == 2
    assert all(log.id != logs[0].id for log in logs)

    unify.delete_logs(logs=logs[1:])
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
    unify.create_fields([field_name])
    fields = unify.get_fields()
    assert field_name in fields

    new_field_name = "first_name"
    unify.rename_field(name=field_name, new_name=new_field_name)

    fields = unify.get_fields()
    assert new_field_name in fields
    assert field_name not in fields


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
    unify.create_fields(fields={field_name: None})
    fields = unify.get_fields()
    assert field_name in fields

    unify.log(first_name="John")
    assert len(unify.get_logs()) == 1

    unify.delete_fields([field_name])
    assert len(unify.get_logs()) == 0

    fields = unify.get_fields()
    assert field_name not in fields


if __name__ == "__main__":
    pass
