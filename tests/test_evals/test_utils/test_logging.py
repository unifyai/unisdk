import pytest
from requests import HTTPError

import unify


def test_log():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    data = {
        "system_prompt": "You are a weather assistant",
        "user_prompt": "hello world",
    }
    assert len(unify.get_logs(project=project)) == 0
    log_id = unify.log(project=project, **data).id
    project_logs = unify.get_logs(project=project)
    assert len(project_logs) and project_logs[0].id == log_id
    id_log = unify.get_log_by_id(log_id)
    assert len(id_log) and "user_prompt" in id_log.entries
    unify.delete_log_fields(field="user_prompt", logs=log_id)
    id_log = unify.get_log_by_id(log_id)
    assert len(id_log) and "user_prompt" not in id_log.entries
    unify.add_log_entries(logs=log_id, user_prompt=data["user_prompt"])
    id_log = unify.get_log_by_id(log_id)
    assert len(id_log) and "user_prompt" in id_log.entries
    unify.delete_logs(logs=log_id)
    assert len(unify.get_logs(project=project)) == 0
    try:
        unify.get_log_by_id(log_id)
        assert False
    except HTTPError as e:
        assert e.response.status_code == 404


def test_log_dataset():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.log(
        project=project,
        dataset=unify.Dataset(["a", "b", "c"], name="letters"),
    )
    logs = unify.get_logs(project=project)
    assert len(logs) == 1
    assert logs[0].entries == {"dataset": "letters"}
    downloaded = unify.download_dataset("letters")
    assert len(downloaded) == 3
    logs[0].delete()
    unify.delete_dataset("letters")


def test_log_skip_duplicates():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    data = {
        "system_prompt": "You are a weather assistant",
        "user_prompt": "hello world",
    }
    assert len(unify.get_logs(project=project)) == 0
    log0 = unify.log(project=project, **data)
    log1 = unify.log(project=project, **data)
    assert log0 == log1
    assert len(unify.get_logs_by_value(project=project, **data)) == 1
    log0.delete()
    assert len(unify.get_logs_by_value(project=project, **data)) == 0


def test_duplicate_log_field():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    data = {
        "system_prompt": "You are a weather assistant",
        "user_prompt": "hello world",
    }
    assert len(unify.get_logs(project=project)) == 0
    log = unify.log(project=project, **data)
    assert len(unify.get_logs(project=project)) == 1
    new_data = {
        "system_prompt": "You are a maths assistant",
        "user_prompt": "hi earth",
    }
    with pytest.raises(Exception):
        log.add_entries(**new_data)


def test_log_function_logs_code():

    def my_func(a):
        return a + 1

    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.log(project=project, my_func=my_func)
    logs = unify.get_logs(project=project)
    assert len(logs) == 1
    assert logs[0].entries["my_func"] == "    def my_func(a):\n        return a + 1\n"


def test_atomic_functions():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
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
    unify.log(project=project, **log1)
    unify.log(project=project, **log2)
    unify.log(project=project, **log3)
    grouped_logs = unify.group_logs(key="system_prompt", project=project)
    assert len(grouped_logs) == 2
    assert sorted([version for version in grouped_logs]) == ["0", "1"]

    logs_metric = unify.get_logs_metric(
        metric="mean",
        key="score",
        filter="'hello' in user_prompt",
        project="my_project",
    )
    assert logs_metric == 0.25


def test_log_ordering():
    project = "test_project_log_ordering"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    for i in range(25):
        unify.log(
            project=project,
            a=i,
            b=i + 1,
            c=i + 2,
        )
    logs = unify.get_logs(project=project)
    for lg in logs:
        assert list(lg.entries.keys()) == ["a", "b", "c"]


def test_get_logs():
    project = "test_project_get_logs"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    logs = unify.get_logs(project=project)
    assert len(logs) == 0, "There should be no logs initially."
    log_data1 = {
        "system_prompt": "You are a weather assistant",
        "user_prompt": "What is the weather today?",
        "score": 0.9,
    }
    unify.log(project=project, **log_data1)
    log_data2 = {
        "system_prompt": "You are a travel assistant",
        "user_prompt": "What is the best route to the airport?",
        "score": 0.7,
    }
    unify.log(project=project, **log_data2)
    log_data3 = {
        "system_prompt": "You are a travel assistant",
        "user_prompt": "What is the best route to the airport?",
        "score": 0.2,
    }
    unify.log(project=project, **log_data3)

    logs = unify.get_logs(project=project)
    assert len(logs) == 3, "There should be 3 logs in the project."
    filtered_logs = unify.get_logs(
        project=project,
        filter="'weather' in user_prompt",
    )
    assert (
        len(filtered_logs) == 1
    ), "There should be 1 log with 'weather' in the user prompt."
    assert (
        filtered_logs[0].entries.get("user_prompt") == log_data1["user_prompt"]
    ), "The filtered log should be the one that asks about the weather."
    nonexistent_logs = unify.get_logs(
        project=project,
        filter="'nonexistent' in user_prompt",
    )
    assert (
        len(nonexistent_logs) == 0
    ), "There should be no logs matching the nonexistent filter."
    multiple_filtered_logs = unify.get_logs(
        project=project,
        filter="'travel' in system_prompt and score < 0.5",
    )
    assert (
        len(multiple_filtered_logs) == 1
    ), "There should be 1 log with 'travel' in the user prompt and score > 0.5."
    bracket_logs = unify.get_logs(
        project=project,
        filter="('weather' in user_prompt) and ('weather' in system_prompt)",
    )
    assert (
        len(bracket_logs) == 1
    ), "There should be 1 log with 'weather' in the user prompt and system prompt."
    assert (
        bracket_logs[0].entries.get("user_prompt") == log_data1["user_prompt"]
    ), "The filtered log should be the one that asks about the weather."
    comparison_logs = unify.get_logs(project=project, filter="score > 0.5")
    assert len(comparison_logs) == 2, "There should be 2 logs with score > 0.5."
    comparison_logs = unify.get_logs(project=project, filter="score == 0.9")
    assert len(comparison_logs) == 1, "There should be 1 log with score == 0.9."
    logical_logs = unify.get_logs(
        project=project,
        filter="score > 0.5 and score < 0.8",
    )
    assert (
        len(logical_logs) == 1
    ), "There should be 1 log with score > 0.5 and score < 0.8."
    logical_logs = unify.get_logs(
        project=project,
        filter="score < 0.5 or score > 0.8",
    )
    assert (
        len(logical_logs) == 2
    ), "There should be 2 logs with score < 0.5 or score > 0.8."
    string_comparison_logs = unify.get_logs(
        project=project,
        filter="user_prompt == 'What is the weather today?'",
    )
    assert (
        len(string_comparison_logs) == 1
    ), "There should be 1 log with user_prompt == 'What is the weather today?'."
    unify.delete_project(project)


def test_delete_logs():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    assert len(unify.get_logs(project=project)) == 0
    unify.log(project=project, customer="John Smith")
    unify.log(project=project, customer="Maggie Smith")
    unify.log(project=project, customer="John Terry")
    assert len(unify.get_logs(project=project)) == 3
    deleted_logs = unify.delete_logs_by_value(
        project=project,
        filter="'Smith' in customer",
    )
    assert len(deleted_logs) == 2
    assert set([dl.entries["customer"] for dl in deleted_logs]) == {
        "John Smith",
        "Maggie Smith",
    }
    assert len(unify.get_logs(project=project)) == 1
    deleted_logs = unify.delete_logs_by_value(project=project)
    assert len(deleted_logs) == 1
    assert deleted_logs[0].entries["customer"] == "John Terry"
    assert len(unify.get_logs(project=project)) == 0


if __name__ == "__main__":
    pass
