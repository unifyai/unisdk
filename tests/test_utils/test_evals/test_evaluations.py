import unittest

import unify
from requests import HTTPError


class TestEvaluations(unittest.TestCase):

    def test_project(self):
        name = "my_project"
        if name in unify.list_projects():
            unify.delete_project(name)
        assert unify.list_projects() == []
        unify.create_project(name)
        assert name in unify.list_projects()
        new_name = "my_project1"
        unify.rename_project(name, new_name)
        assert new_name in unify.list_projects()
        unify.delete_project(new_name)
        assert unify.list_projects() == []

    def test_artifacts(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        artifacts = {"dataset": "my_dataset", "description": "this is my dataset"}
        assert len(unify.get_artifacts(project)) == 0
        unify.add_artifacts(project=project, **artifacts)
        assert "dataset" in unify.get_artifacts(project)
        unify.delete_artifact(
            "dataset",
            project,
        )
        assert "dataset" not in unify.get_artifacts(project)
        assert "description" in unify.get_artifacts(project)

    def test_log(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        version = {
            "system_prompt": "v1",
        }
        log = {
            "system_prompt": "You are a weather assistant",
            "user_prompt": "hello world",
        }
        assert len(unify.get_logs(project)) == 0
        log_id = unify.log(project, version, **log).id
        project_logs = unify.get_logs(project)
        assert len(project_logs) and project_logs[0].id == log_id
        id_log = unify.get_log(log_id)
        assert len(id_log) and "user_prompt" in id_log.entries
        unify.delete_log_entry("user_prompt", log_id)
        id_log = unify.get_log(log_id)
        assert len(id_log) and "user_prompt" not in id_log.entries
        unify.add_log_entries(log_id, user_prompt=log["user_prompt"])
        id_log = unify.get_log(log_id)
        assert len(id_log) and "user_prompt" in id_log.entries
        unify.delete_log(log_id)
        assert len(unify.get_logs(project)) == 0
        try:
            unify.get_log(log_id)
            assert False
        except HTTPError as e:
            assert e.response.status_code == 404

    def test_atomic_functions(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        version1 = {
            "system_prompt": "v1",
        }
        log1 = {
            "system_prompt": "You are a weather assistant",
            "user_prompt": "hello world",
            "score": 0.2,
        }
        version2 = {
            "system_prompt": "v2",
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
        unify.log(project, version1, **log1)
        unify.log(project, version2, **log2)
        unify.log(project, version2, **log3)
        grouped_logs = unify.group_logs("system_prompt", project)
        assert len(grouped_logs) == 2
        assert sorted([version for version in grouped_logs]) == ["v1", "v2"]

        logs_metric = unify.get_logs_metric(
            "mean",
            "score",
            filter="'hello' in user_prompt",
            project="my_project",
        )
        assert logs_metric == 0.25

    def test_get_logs(self):
        project = "test_project_get_logs"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)

        # Initially, no logs should exist in the project
        logs = unify.get_logs(project)
        assert len(logs) == 0, "There should be no logs initially."

        # Add a log
        log_data1 = {
            "system_prompt": "You are a weather assistant",
            "user_prompt": "What is the weather today?",
            "score": 0.9,
        }
        log1 = unify.log(project=project, **log_data1)

        # Add another log
        log_data2 = {
            "system_prompt": "You are a travel assistant",
            "user_prompt": "What is the best route to the airport?",
            "score": 0.7,
        }
        log2 = unify.log(project=project, **log_data2)

        # Get logs without any filtering
        logs = unify.get_logs(project)
        assert len(logs) == 2, "There should be 2 logs in the project."
        assert logs[0].entries == log1.entries or logs[1].entries == log1.entries, \
            "The first log should match the first log entries."
        assert logs[0].entries == log2.entries or logs[1].entries == log2.entries, \
            "The second log should match the second log entries."

        # Test filtering the logs (e.g., only logs with `"weather"` in `user_prompt`)
        filtered_logs = unify.get_logs(project, filter="'weather' in user_prompt")
        assert len(filtered_logs) == 1, "There should be 1 log with 'weather' in the user prompt."
        assert filtered_logs[0].entries.get("user_prompt") == log_data1["user_prompt"], \
            "The filtered log should be the one that asks about the weather."

        # Test filtering for a nonexistent condition
        nonexistent_logs = unify.get_logs(project, filter="'nonexistent' in user_prompt")
        assert len(nonexistent_logs) == 0, "There should be no logs matching the nonexistent filter."

        # Clean up by deleting the project
        unify.delete_project(project)