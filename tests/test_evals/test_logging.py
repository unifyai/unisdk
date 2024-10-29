import unittest
import time
import asyncio

import unify
import threading


class TestLogging(unittest.TestCase):

    def test_get_log_by_value(self):
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
        retrieved_log = unify.get_log_by_value(project=project, **data)
        assert log == retrieved_log
        log.delete()
        assert unify.get_log_by_value(project=project, **data) is None

    def test_get_logs_by_value(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        data = {
            "system_prompt": "You are a weather assistant",
            "user_prompt": "hello world",
        }
        assert len(unify.get_logs(project=project)) == 0
        log0 = unify.log(project=project, **data, skip_duplicates=False)
        log1 = unify.log(project=project, **data, skip_duplicates=False)
        retrieved_logs = unify.get_logs_by_value(project=project, **data)
        assert len(retrieved_logs) == 2
        for log, retrieved_log in zip((log0, log1), retrieved_logs):
            assert log == retrieved_log
        log0.delete()
        retrieved_logs = unify.get_logs_by_value(project=project, **data)
        assert len(retrieved_logs) == 1
        assert log1 == retrieved_logs[0]
        log1.delete()
        assert unify.get_logs_by_value(project=project, **data) == []

    def test_replace_log_entries(self):
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
        assert unify.get_log_by_id(log.id).entries == data
        assert len(unify.get_logs(project=project)) == 1
        new_data = {
            "system_prompt": "You are a maths assistant",
            "user_prompt": "hi earth",
        }
        log.replace_entries(**new_data)
        assert log.entries == new_data
        assert len(unify.get_logs(project=project)) == 1
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
        assert len(unify.get_logs(project=project)) == 0
        log = unify.log(project=project, messages=messages)
        assert len(unify.get_logs(project=project)) == 1
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
        assert len(unify.get_logs(project=project)) == 1
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
        assert len(unify.get_logs(project=project)) == 0
        log = unify.log(project=project, messages=messages, name=name)
        assert len(unify.get_logs(project=project)) == 1
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
        assert log.entries["messages"] == combined_messages
        assert len(unify.get_logs(project=project)) == 1
        assert unify.get_log_by_id(log.id).entries["messages"] == combined_messages

    def test_rename_log_entries(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        customer = "John Smith"
        assert len(unify.get_logs(project=project)) == 0
        log = unify.log(project=project, customer=customer)
        assert len(unify.get_logs(project=project)) == 1
        assert unify.get_log_by_id(log.id).entries["customer"] == customer
        log.rename_entries(customer="customer_name")
        assert "customer" not in log.entries
        assert "customer_name" in log.entries
        assert len(unify.get_logs(project=project)) == 1
        retrieved_log = unify.get_log_by_id(log.id)
        assert "customer" not in retrieved_log.entries
        assert "customer_name" in retrieved_log.entries

    def test_get_logs_with_fields(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        assert len(unify.get_logs(project=project)) == 0
        unify.log(project=project, customer="John Smith")
        assert len(unify.get_logs_with_fields("customer", project=project)) == 1
        assert len(unify.get_logs_with_fields("dummy", project=project)) == 0
        unify.log(project=project, seller="Maggie Jones")
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

    def test_get_logs_without_fields(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        assert len(unify.get_logs(project=project)) == 0
        unify.log(project=project, customer="John Smith")
        assert len(unify.get_logs_without_fields("customer", project=project)) == 0
        assert len(unify.get_logs_without_fields("dummy", project=project)) == 1
        unify.log(project=project, seller="Maggie Jones")
        assert (
            len(
                unify.get_logs_without_fields(
                    "customer",
                    "seller",
                    mode="all",
                    project=project,
                ),
            )
            == 2
        )
        assert (
            len(
                unify.get_logs_without_fields(
                    "customer",
                    "seller",
                    mode="any",
                    project=project,
                ),
            )
            == 0
        )

    def test_group_logs_by_params(self):
        logs = list()
        log_idx = 0
        qs = ["1+1", "2+2", "3+3", "4+1"]
        for system_prompt in ["You are an expert.", "You are an expert mathematician."]:
            for dataset_version in ["vanilla", "with_failures", "with_successes"]:
                params = dict(
                    system_prompt=system_prompt,
                    dataset_version=dataset_version,
                )
                for q in qs:
                    logs.append(unify.Log(log_idx, q=q, parameters=params))
                    log_idx += 1
        grouped_logs = unify.group_logs_by_params(logs=logs)
        assert len(grouped_logs) == 6
        assert list(grouped_logs.keys()) == [
            '{"system_prompt": "You are an expert.", ' '"dataset_version": "vanilla"}',
            '{"system_prompt": "You are an expert.", '
            '"dataset_version": "with_failures"}',
            '{"system_prompt": "You are an expert.", '
            '"dataset_version": "with_successes"}',
            '{"system_prompt": "You are an expert mathematician.", '
            '"dataset_version": "vanilla"}',
            '{"system_prompt": "You are an expert mathematician.", '
            '"dataset_version": "with_failures"}',
            '{"system_prompt": "You are an expert mathematician.", '
            '"dataset_version": "with_successes"}',
        ]

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

        logs = unify.get_logs(project="my_project")
        list1 = [log.entries for log in logs]
        list2 = [{"d1": "Thread-1", "d2": "data1"}, {"d1": "Thread-2", "d2": "data2"}]

        # Sort each dictionary by keys and then sort the list
        assert sorted([sorted(d.items()) for d in list1]) == sorted(
            [sorted(d.items()) for d in list2],
        )

    def test_with_entries(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        unify.activate(project)

        with unify.Entries(context="random"):
            log = unify.log(a="a")
            with unify.Entries(sys="sys"):
                unify.add_log_entries(logs=log.id, q="some q", r="some r")
            with unify.Entries(tool="tool"):
                unify.add_log_entries(logs=log.id, t="some t", b="some b")

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

    def test_span(self):
        project = "my_project"
        if project in unify.list_projects():
            unify.delete_project(project)
        unify.create_project(project)
        unify.activate(project)

        @unify.span()
        def deeper_fn():
            time.sleep(1)
            return 3

        @unify.span()
        def inner_fn():
            time.sleep(1)
            deeper_fn()
            return 2

        @unify.span()
        def some_func(st):
            time.sleep(st)
            inner_fn()
            inner_fn()
            return 1

        some_func(0.5)
        log = unify.get_logs(project="my_project")[0].entries

        assert log["trace"]["inputs"] == {"st": 0.5}
        assert log["trace"]["span_name"] == "some_func"
        assert len(log["trace"]["child_spans"]) == 2
        assert log["trace"]["child_spans"][0]["span_name"] == "inner_fn"
        assert len(log["trace"]["child_spans"][0]["child_spans"]) == 1
        assert (
            log["trace"]["child_spans"][0]["child_spans"][0]["span_name"] == "deeper_fn"
        )


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

        logs = unify.get_logs(project="my_project")
        list1 = [log.entries for log in logs]
        list2 = [{"d1": "Task-1", "d2": "data1"}, {"d1": "Task-2", "d2": "data2"}]

        # Sort each dictionary by keys and then sort the list
        assert sorted([sorted(d.items()) for d in list1]) == sorted(
            [sorted(d.items()) for d in list2],
        )
