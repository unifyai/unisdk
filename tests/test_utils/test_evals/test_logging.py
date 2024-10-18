import unittest
import time
import asyncio

import unify
from requests import HTTPError
import threading


class TestLogging(unittest.TestCase):

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
        data = {
            "system_prompt": "You are a weather assistant",
            "user_prompt": "hello world",
        }
        assert len(unify.get_logs(project)) == 0
        log_id = unify.log(project, version, **data).id
        project_logs = unify.get_logs(project)
        assert len(project_logs) and project_logs[0].id == log_id
        id_log = unify.get_log_by_id(log_id)
        assert len(id_log) and "user_prompt" in id_log.entries
        unify.delete_log_entry("user_prompt", log_id)
        id_log = unify.get_log_by_id(log_id)
        assert len(id_log) and "user_prompt" not in id_log.entries
        unify.add_log_entries(log_id, user_prompt=data["user_prompt"])
        id_log = unify.get_log_by_id(log_id)
        assert len(id_log) and "user_prompt" in id_log.entries
        unify.delete_log(log_id)
        assert len(unify.get_logs(project)) == 0
        try:
            unify.get_log_by_id(log_id)
            assert False
        except HTTPError as e:
            assert e.response.status_code == 404

    def test_get_log_by_value(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        data = {
            "system_prompt": "You are a weather assistant",
            "user_prompt": "hello world",
        }
        assert len(unify.get_logs(project)) == 0
        log = unify.log(project, **data)
        retrieved_log = unify.get_log_by_value(project, **data)
        assert log == retrieved_log
        log.delete()
        assert unify.get_log_by_value(project, **data) is None

    def test_get_logs_by_value(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        data = {
            "system_prompt": "You are a weather assistant",
            "user_prompt": "hello world",
        }
        assert len(unify.get_logs(project)) == 0
        log0 = unify.log(project, **data, skip_duplicates=False)
        log1 = unify.log(project, **data, skip_duplicates=False)
        retrieved_logs = unify.get_logs_by_value(project, **data)
        assert len(retrieved_logs) == 2
        for log, retrieved_log in zip((log0, log1), retrieved_logs):
            assert log == retrieved_log
        log0.delete()
        retrieved_logs = unify.get_logs_by_value(project, **data)
        assert len(retrieved_logs) == 1
        assert log1 == retrieved_logs[0]
        log1.delete()
        assert unify.get_logs_by_value(project, **data) == []

    def test_log_skip_duplicates(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        data = {
            "system_prompt": "You are a weather assistant",
            "user_prompt": "hello world",
        }
        assert len(unify.get_logs(project)) == 0
        log0 = unify.log(project, **data)
        log1 = unify.log(project, **data)
        assert log0 == log1
        assert len(unify.get_logs_by_value(project, **data)) == 1
        log0.delete()
        assert len(unify.get_logs_by_value(project, **data)) == 0

    def test_duplicate_log_field(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        data = {
            "system_prompt": "You are a weather assistant",
            "user_prompt": "hello world",
        }
        assert len(unify.get_logs(project)) == 0
        log = unify.log(project, **data)
        assert len(unify.get_logs(project)) == 1
        new_data = {
            "system_prompt": "You are a maths assistant",
            "user_prompt": "hi earth",
        }
        with self.assertRaises(Exception):
            log.add_entries(**new_data)

    def test_replace_log_entries(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        data = {
            "system_prompt": "You are a weather assistant",
            "user_prompt": "hello world",
        }
        assert len(unify.get_logs(project)) == 0
        log = unify.log(project, **data)
        assert unify.get_log_by_id(log.id).entries == data
        assert len(unify.get_logs(project)) == 1
        new_data = {
            "system_prompt": "You are a maths assistant",
            "user_prompt": "hi earth",
        }
        log.replace_entries(**new_data)
        assert log.entries == new_data
        assert len(unify.get_logs(project)) == 1
        assert unify.get_log_by_id(log.id).entries == new_data

    def test_update_log_entries(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        messages = [
            {
                "role": "assistant",
                "context": "you are a helpful assistant",
            },
        ]
        assert len(unify.get_logs(project)) == 0
        log = unify.log(project, messages=messages)
        assert len(unify.get_logs(project)) == 1
        assert unify.get_log_by_id(log.id).entries["messages"] == messages
        new_messages = [
            {
                "role": "user",
                "context": "what is 1 + 1?",
            },
        ]
        log.update_entries(lambda x, y: x + y, messages=new_messages)
        combined_messages = messages + new_messages
        assert log.entries["messages"] == combined_messages
        assert len(unify.get_logs(project)) == 1
        assert unify.get_log_by_id(log.id).entries["messages"] == combined_messages

    def test_update_log_entries_w_dict(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        messages = [
            {
                "role": "assistant",
                "context": "you are a helpful assistant",
            },
        ]
        name = "John"
        assert len(unify.get_logs(project)) == 0
        log = unify.log(project, messages=messages, name=name)
        assert len(unify.get_logs(project)) == 1
        assert unify.get_log_by_id(log.id).entries["messages"] == messages
        new_messages = [
            {
                "role": "user",
                "context": "what is 1 + 1?",
            },
        ]
        surname = "Smith"
        log.update_entries(
            {
                "messages": lambda x, y: x + y,
                "name": lambda x, y: f"{x} {y}",
            },
            messages=new_messages,
            name=surname,
        )
        combined_messages = messages + new_messages
        assert log.entries == combined_messages
        assert len(unify.get_logs(project)) == 1
        assert unify.get_log_by_id(log.id).entries == combined_messages

    def test_rename_log_entries(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        customer = "John Smith"
        assert len(unify.get_logs(project)) == 0
        log = unify.log(project, customer=customer)
        assert len(unify.get_logs(project)) == 1
        assert unify.get_log_by_id(log.id).entries["customer"] == customer
        log.rename_entries(customer="customer_name")
        assert "customer" not in log.entries
        assert "customer_name" in log.entries
        assert len(unify.get_logs(project)) == 1
        retrieved_log = unify.get_log_by_id(log.id)
        assert "customer" not in retrieved_log.entries
        assert "customer_name" in retrieved_log.entries

    def test_version_log_entries(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        customer = "John Smith"
        assert len(unify.get_logs(project)) == 0
        log = unify.log(project, customer=customer)
        assert len(unify.get_logs(project)) == 1
        assert unify.get_log_by_id(log.id).entries["customer"] == customer
        log.version_entries(customer=0)
        assert "customer" not in log.entries
        assert "customer/0" in log.entries
        assert len(unify.get_logs(project)) == 1
        retrieved_log = unify.get_log_by_id(log.id)
        assert "customer" not in retrieved_log.entries
        assert "customer/0" in retrieved_log.entries

    def test_unversion_log_entries(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        customer = "John Smith"
        assert len(unify.get_logs(project)) == 0
        log = unify.log(project, customer=customer, version=0)
        assert len(unify.get_logs(project)) == 1
        assert unify.get_log_by_id(log.id).entries["customer/0"] == customer
        log.unversion_entries("customer/0")
        assert "customer/0" not in log.entries
        assert "customer" in log.entries
        assert len(unify.get_logs(project)) == 1
        retrieved_log = unify.get_log_by_id(log.id)
        assert "customer/0" not in retrieved_log.entries
        assert "customer" in retrieved_log.entries

    def test_reversion_log_entries(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        customer = "John Smith"
        assert len(unify.get_logs(project)) == 0
        log = unify.log(project, customer=customer, version=0)
        assert len(unify.get_logs(project)) == 1
        assert unify.get_log_by_id(log.id).entries["customer/0"] == customer
        log.reversion_entries(customer=(0, 1))
        assert "customer/0" not in log.entries
        assert "customer/1" in log.entries
        assert len(unify.get_logs(project)) == 1
        retrieved_log = unify.get_log_by_id(log.id)
        assert "customer/0" not in retrieved_log.entries
        assert "customer/1" in retrieved_log.entries

    def test_get_logs_with_fields(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        assert len(unify.get_logs(project)) == 0
        unify.log(project, customer="John Smith")
        assert len(unify.get_logs_with_fields("customer", project=project)) == 1
        assert len(unify.get_logs_with_fields("dummy", project=project)) == 0
        unify.log(project, seller="Maggie Jones")
        assert (
            len(
                unify.get_logs_with_fields(
                    "customer",
                    "seller",
                    mode="all",
                    project=project,
                ),
            )
            == 0
        )
        assert (
            len(
                unify.get_logs_with_fields(
                    "customer",
                    "seller",
                    mode="any",
                    project=project,
                ),
            )
            == 2
        )

    def test_project_thread_lock(self):
        # all 10 threads would try to create the project at the same time without
        # thread locking, but only will should acquire the lock, and this should pass
        unify.map(unify.log, project="test_project", a=[1] * 10, b=[2] * 10, c=[3] * 10)
        unify.delete_project("test_project")

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
        logs = unify.get_logs(project)
        assert len(logs) == 0, "There should be no logs initially."
        log_data1 = {
            "system_prompt": "You are a weather assistant",
            "user_prompt": "What is the weather today?",
            "score": 0.9,
        }
        log1 = unify.log(project=project, **log_data1)
        log_data2 = {
            "system_prompt": "You are a travel assistant",
            "user_prompt": "What is the best route to the airport?",
            "score": 0.7,
        }
        log2 = unify.log(project=project, **log_data2)
        log_data3 = {
            "system_prompt": "You are a travel assistant",
            "user_prompt": "What is the best route to the airport?",
            "score": 0.2,
        }
        log3 = unify.log(project=project, **log_data3)

        logs = unify.get_logs(project)
        assert len(logs) == 3, "There should be 3 logs in the project."
        filtered_logs = unify.get_logs(project, filter="'weather' in user_prompt")
        assert (
            len(filtered_logs) == 1
        ), "There should be 1 log with 'weather' in the user prompt."
        assert (
            filtered_logs[0].entries.get("user_prompt") == log_data1["user_prompt"]
        ), "The filtered log should be the one that asks about the weather."
        nonexistent_logs = unify.get_logs(
            project,
            filter="'nonexistent' in user_prompt",
        )
        assert (
            len(nonexistent_logs) == 0
        ), "There should be no logs matching the nonexistent filter."
        multiple_filtered_logs = unify.get_logs(
            project,
            filter="'travel' in system_prompt and score < 0.5",
        )
        assert (
            len(multiple_filtered_logs) == 1
        ), "There should be 1 log with 'travel' in the user prompt and score > 0.5."
        bracket_logs = unify.get_logs(
            project,
            filter="('weather' in user_prompt) and ('weather' in system_prompt)",
        )
        assert (
            len(bracket_logs) == 1
        ), "There should be 1 log with 'weather' in the user prompt and system prompt."
        assert (
            bracket_logs[0].entries.get("user_prompt") == log_data1["user_prompt"]
        ), "The filtered log should be the one that asks about the weather."
        comparison_logs = unify.get_logs(project, filter="score > 0.5")
        assert len(comparison_logs) == 2, "There should be 2 logs with score > 0.5."
        comparison_logs = unify.get_logs(project, filter="score == 0.9")
        assert len(comparison_logs) == 1, "There should be 1 log with score == 0.9."
        logical_logs = unify.get_logs(project, filter="score > 0.5 and score < 0.8")
        assert (
            len(logical_logs) == 1
        ), "There should be 1 log with score > 0.5 and score < 0.8."
        logical_logs = unify.get_logs(project, filter="score < 0.5 or score > 0.8")
        assert (
            len(logical_logs) == 2
        ), "There should be 2 logs with score < 0.5 or score > 0.8."
        string_comparison_logs = unify.get_logs(
            project,
            filter="user_prompt == 'What is the weather today?'",
        )
        assert (
            len(string_comparison_logs) == 1
        ), "There should be 1 log with user_prompt == 'What is the weather today?'."
        unify.delete_project(project)

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


class TestAsyncLogging(unittest.IsolatedAsyncioTestCase):
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
