import unittest
import time
import asyncio

import unify
from requests import HTTPError
import threading


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

    def test_contextual_logging_threaded(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        unify.activate(project)

        def inner_fn(data, st):
            time.sleep(st)
            unify.add_log_entries(d2=data)

        @unify.trace()
        def fn1(data1, data2, st):
            unify.add_log_entries(d1=data1)
            inner_fn(data2, st)

        thread1 = threading.Thread(target=fn1, args=("Thread-1", "data1", 1))
        thread2 = threading.Thread(target=fn1, args=("Thread-2", "data2", 2))

        # Start the threads
        thread1.start()
        thread2.start()

        # Wait for both threads to complete
        thread1.join()
        thread2.join()

        logs = unify.get_logs("my_project")
        list1 = [log.entries for log in logs]
        list2 = [{"d1": "Thread-1", "d2": "data1"}, {"d1": "Thread-2", "d2": "data2"}]

        # Sort each dictionary by keys and then sort the list
        assert sorted([sorted(d.items()) for d in list1]) == sorted(
            [sorted(d.items()) for d in list2],
        )

    def test_with_Context(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        unify.activate(project)

        with unify.Context(context="random"):
            log = unify.log(a="a")
            with unify.Context(sys="sys"):
                unify.add_log_entries(log.id, q="some q", r="some r")
            with unify.Context(tool="tool"):
                unify.add_log_entries(log.id, t="some t", b="some b")

        expected = {
            "context": "random",
            "a": "a",
            "q": "some q",
            "t": "some t",
            "b": "some b",
            "r": "some r",
            "sys": "sys",
            "tool": "tool",
        }
        log = unify.get_logs()[0].entries
        assert expected == log


class TestAsyncEvaluations(unittest.IsolatedAsyncioTestCase):
    async def test_contextual_logging_async(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        unify.activate(project)

        async def inner_fn(data, st):
            await asyncio.sleep(st)
            unify.add_log_entries(d2=data)

        @unify.trace()
        async def fn1(data1, data2, st):
            unify.add_log_entries(d1=data1)
            await inner_fn(data2, st)

        await asyncio.gather(fn1("Task-1", "data1", 1), fn1("Task-2", "data2", 2))

        logs = unify.get_logs("my_project")
        list1 = [log.entries for log in logs]
        list2 = [{"d1": "Task-1", "d2": "data1"}, {"d1": "Task-2", "d2": "data2"}]

        # Sort each dictionary by keys and then sort the list
        assert sorted([sorted(d.items()) for d in list1]) == sorted(
            [sorted(d.items()) for d in list2],
        )
