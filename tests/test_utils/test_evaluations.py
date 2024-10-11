from requests import HTTPError
import unify
import unittest


class TestEvaluations(unittest.TestCase):

    def test_project(self):
        assert unify.list_projects() == []
        name = "my_project"
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
        assert len(project_logs) and project_logs[0]["id"] == log_id
        id_log = unify.get_log(log_id)
        assert len(id_log) and "user_prompt" in id_log["entries"]
        unify.delete_log_entry("user_prompt", log_id)
        id_log = unify.get_log(log_id)
        assert len(id_log) and "user_prompt" not in id_log["entries"]
        unify.add_log_entries(log_id, user_prompt=log["user_prompt"])
        id_log = unify.get_log(log_id)
        assert len(id_log) and "user_prompt" in id_log["entries"]
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
        assert [version for version in grouped_logs].sort() == ["v1", "v2"]

        logs_metric = unify.get_logs_metric(
            "mean", "score", filter="'hello' in user_prompt"
        )
        assert logs_metric == 0.25
