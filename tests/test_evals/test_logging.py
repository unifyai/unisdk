import os
import time
import math
import asyncio
import pytest

import unify
import threading


# Functional Compositions #
# ------------------------#


def test_get_log_by_value():
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


def test_get_logs_by_value():
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


def test_replace_log_entries():
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


def test_update_log_entries():
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


def test_update_log_entries_w_dict():
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


def test_rename_log_entries():
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


def test_get_logs_with_fields():
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


def test_get_logs_without_fields():
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


def test_group_logs_by_params():
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
                logs.append(unify.Log(id=log_idx, q=q, params=params))
                log_idx += 1
    grouped_logs = unify.group_logs_by_configs(logs=logs)
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


# Context Handlers #
# -----------------#

# Log


def test_with_log():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

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
            assert logs[1].entries == {"d": "d"}
            unify.add_log_entries(e="e", f="f")
            logs = unify.get_logs()
            assert len(logs) == 2
            assert logs[1].entries == {"d": "d", "e": "e", "f": "f"}
        unify.add_log_entries(g="g")
        logs = unify.get_logs()
        assert len(logs) == 2
        assert logs[0].entries == {"a": "a", "b": "b", "c": "c", "g": "g"}


def test_global_logging():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

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
            assert logs[1].entries == {"d": "d"}
            unify.log(e="e", f="f")
            logs = unify.get_logs()
            assert len(logs) == 2
            assert logs[1].entries == {"d": "d", "e": "e", "f": "f"}
        unify.log(g="g")
        logs = unify.get_logs()
        assert len(logs) == 2
        assert logs[0].entries == {"a": "a", "b": "b", "c": "c", "g": "g"}


def test_with_log_threaded():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

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

    logs = unify.get_logs(project="my_project")
    entries = [log.entries for log in logs]

    assert sorted([sorted(d.items()) for d in entries]) == [
        [("a", i * 7), ("b", i * 7 + 1), ("c", i * 7 + 2), ("g", i * 7 + 6)]
        for i in range(4)
    ] + [[("d", i * 7 + 3), ("e", i * 7 + 4), ("f", i * 7 + 5)] for i in range(4)]


@pytest.mark.asyncio
async def test_with_log_async():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

    async def fn(a, b, c, d, e, f, g):
        with unify.Log(a=a):
            unify.add_log_entries(b=b, c=c)
            with unify.Log(d=d):
                unify.add_log_entries(e=e, f=f)
            unify.add_log_entries(g=g)

    fns = [fn(*[7 * i + j for j in range(7)]) for i in range(4)]
    await asyncio.gather(*fns)

    logs = unify.get_logs(project="my_project")
    entries = [log.entries for log in logs]

    assert sorted([sorted(d.items()) for d in entries]) == [
        [("a", i * 7), ("b", i * 7 + 1), ("c", i * 7 + 2), ("g", i * 7 + 6)]
        for i in range(4)
    ] + [[("d", i * 7 + 3), ("e", i * 7 + 4), ("f", i * 7 + 5)] for i in range(4)]


# Context


def test_with_context():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

    unify.log(project=project, a="a")
    logs = unify.get_logs()
    assert len(logs) == 1
    assert logs[0].entries == {"a": "a"}
    with unify.Context("capitalized"):
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].entries == {"a": "a"}
        unify.add_log_entries(logs=logs, b="B")
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].entries == {"a": "a", "capitalized/b": "B"}
        with unify.Context("vowels"):
            logs = unify.get_logs()
            assert len(logs) == 1
            assert logs[0].entries == {"a": "a", "capitalized/b": "B"}
            unify.add_log_entries(logs=logs, e="E")
            unify.add_log_params(logs=logs, u="U")
            logs = unify.get_logs()
            assert len(logs) == 1
            assert logs[0].entries == {
                "a": "a",
                "capitalized/b": "B",
                "capitalized/vowels/e": "E",
            }
            assert logs[0].params == {
                "capitalized/vowels/u": "U",
            }
            unify.log(project=project, a="A")
    logs = unify.get_logs()
    assert len(logs) == 2
    assert logs[0].entries == {
        "a": "a",
        "capitalized/b": "B",
        "capitalized/vowels/e": "E",
    }
    assert logs[1].entries == {
        "capitalized/vowels/a": "A",
    }


def test_with_context_threaded():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

    def fn(a, b, e):
        log = unify.log(project=project, a=a)
        with unify.Context("capitalized"):
            log.add_entries(b=b)
            with unify.Context("vowels"):
                log.add_entries(e=e)
                unify.log(project=project, a=a)

    threads = [
        threading.Thread(
            target=fn,
            args=[3 * i + j for j in range(3)],
        )
        for i in range(4)
    ]
    [t.start() for t in threads]
    [t.join() for t in threads]

    logs = unify.get_logs(project="my_project")
    entries = sorted(
        [log.entries for log in logs],
        key=lambda dct: list(dct.values())[0],
    )
    for i, entry in enumerate(entries[0::2]):
        assert entry == {
            "a": i * 3,
            "capitalized/b": i * 3 + 1,
            "capitalized/vowels/e": i * 3 + 2,
        }
    for i, entry in enumerate(entries[1::2]):
        assert entry == {"capitalized/vowels/a": i * 3}


@pytest.mark.asyncio
async def test_with_context_async():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

    async def fn(a, b, e):
        log = unify.log(project=project, a=a)
        with unify.Context("capitalized"):
            log.add_entries(b=b)
            with unify.Context("vowels"):
                log.add_entries(e=e)
                unify.log(project=project, a=a)

    fns = [fn(*[3 * i + j for j in range(3)]) for i in range(4)]
    await asyncio.gather(*fns)

    logs = unify.get_logs(project="my_project")
    entries = sorted(
        [log.entries for log in logs],
        key=lambda dct: list(dct.values())[0],
    )
    for i, entry in enumerate(entries[0::2]):
        assert entry == {
            "a": i * 3,
            "capitalized/b": i * 3 + 1,
            "capitalized/vowels/e": i * 3 + 2,
        }
    for i, entry in enumerate(entries[1::2]):
        assert entry == {"capitalized/vowels/a": i * 3}


# Entries


def test_with_entries():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

    with unify.Entries(a="a"):
        logs = unify.get_logs()
        assert len(logs) == 0
        log = unify.log()
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].entries == {"a": "a"}
        unify.add_log_entries(logs=log, b="b", c="c")
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].entries == {"a": "a", "b": "b", "c": "c"}
        with unify.Entries(d="d"):
            unify.add_log_entries(logs=log)
            logs = unify.get_logs()
            assert len(logs) == 1
            assert logs[0].entries == {"a": "a", "b": "b", "c": "c", "d": "d"}
            unify.add_log_entries(logs=log, e="e", f="f")
            logs = unify.get_logs()
            assert len(logs) == 1
            assert logs[0].entries == {
                "a": "a",
                "b": "b",
                "c": "c",
                "d": "d",
                "e": "e",
                "f": "f",
            }
        unify.add_log_entries(logs=log, g="g")
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].entries == {
            "a": "a",
            "b": "b",
            "c": "c",
            "d": "d",
            "e": "e",
            "f": "f",
            "g": "g",
        }


def test_with_entries_threaded():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

    def fn(a, b, c, d, e, f, g):
        with unify.Entries(a=a):
            log = unify.log()
            unify.add_log_entries(logs=log, b=b, c=c)
            with unify.Entries(d=d):
                unify.add_log_entries(logs=log)
                unify.add_log_entries(logs=log, e=e, f=f)
            unify.add_log_entries(logs=log, g=g)

    threads = [
        threading.Thread(
            target=fn,
            args=[7 * i + j for j in range(7)],
        )
        for i in range(4)
    ]
    [t.start() for t in threads]
    [t.join() for t in threads]

    logs = unify.get_logs(project="my_project")
    entries = [log.entries for log in logs]

    assert sorted([sorted(d.items()) for d in entries]) == [
        [
            ("a", i * 7),
            ("b", i * 7 + 1),
            ("c", i * 7 + 2),
            ("d", i * 7 + 3),
            ("e", i * 7 + 4),
            ("f", i * 7 + 5),
            ("g", i * 7 + 6),
        ]
        for i in range(4)
    ]


@pytest.mark.asyncio
async def test_with_entries_async():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

    async def fn(a, b, c, d, e, f, g):
        with unify.Entries(a=a):
            log = unify.log()
            unify.add_log_entries(logs=log, b=b, c=c)
            with unify.Entries(d=d):
                unify.add_log_entries(logs=log)
                unify.add_log_entries(logs=log, e=e, f=f)
            unify.add_log_entries(logs=log, g=g)

    fns = [fn(*[7 * i + j for j in range(7)]) for i in range(4)]
    await asyncio.gather(*fns)

    logs = unify.get_logs(project="my_project")
    entries = [log.entries for log in logs]

    assert sorted([sorted(d.items()) for d in entries]) == [
        [
            ("a", i * 7),
            ("b", i * 7 + 1),
            ("c", i * 7 + 2),
            ("d", i * 7 + 3),
            ("e", i * 7 + 4),
            ("f", i * 7 + 5),
            ("g", i * 7 + 6),
        ]
        for i in range(4)
    ]


# Params


def test_with_params():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

    with unify.Params(a="a"):
        logs = unify.get_logs()
        assert len(logs) == 0
        log = unify.log()
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].params == {"a": "a"}
        unify.add_log_params(logs=log, b="b", c="c")
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].params == {"a": "a", "b": "b", "c": "c"}
        with unify.Params(d="d"):
            unify.add_log_params(logs=log)
            logs = unify.get_logs()
            assert len(logs) == 1
            assert logs[0].params == {"a": "a", "b": "b", "c": "c", "d": "d"}
            unify.add_log_params(logs=log, e="e", f="f")
            logs = unify.get_logs()
            assert len(logs) == 1
            assert logs[0].params == {
                "a": "a",
                "b": "b",
                "c": "c",
                "d": "d",
                "e": "e",
                "f": "f",
            }
        unify.add_log_params(logs=log, g="g")
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].params == {
            "a": "a",
            "b": "b",
            "c": "c",
            "d": "d",
            "e": "e",
            "f": "f",
            "g": "g",
        }


def test_with_params_threaded():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

    def fn(a, b, c, d, e, f, g):
        with unify.Params(a=a):
            log = unify.log()
            unify.add_log_params(logs=log, b=b, c=c)
            with unify.Params(d=d):
                unify.add_log_params(logs=log)
                unify.add_log_params(logs=log, e=e, f=f)
            unify.add_log_params(logs=log, g=g)

    threads = [
        threading.Thread(
            target=fn,
            args=[7 * i + j for j in range(7)],
        )
        for i in range(4)
    ]
    [t.start() for t in threads]
    [t.join() for t in threads]

    logs = unify.get_logs(project="my_project")
    params = [log.params for log in logs]

    assert sorted([sorted(d.items()) for d in params]) == [
        [
            ("a", i * 7),
            ("b", i * 7 + 1),
            ("c", i * 7 + 2),
            ("d", i * 7 + 3),
            ("e", i * 7 + 4),
            ("f", i * 7 + 5),
            ("g", i * 7 + 6),
        ]
        for i in range(4)
    ]


@pytest.mark.asyncio
async def test_with_params_async():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

    async def fn(a, b, c, d, e, f, g):
        with unify.Params(a=a):
            log = unify.log()
            unify.add_log_params(logs=log, b=b, c=c)
            with unify.Params(d=d):
                unify.add_log_params(logs=log)
                unify.add_log_params(logs=log, e=e, f=f)
            unify.add_log_params(logs=log, g=g)

    fns = [fn(*[7 * i + j for j in range(7)]) for i in range(4)]
    await asyncio.gather(*fns)

    logs = unify.get_logs(project="my_project")
    params = [log.params for log in logs]

    assert sorted([sorted(d.items()) for d in params]) == [
        [
            ("a", i * 7),
            ("b", i * 7 + 1),
            ("c", i * 7 + 2),
            ("d", i * 7 + 3),
            ("e", i * 7 + 4),
            ("f", i * 7 + 5),
            ("g", i * 7 + 6),
        ]
        for i in range(4)
    ]


# Combos


def test_with_all():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

    with unify.Params(a="a"):
        logs = unify.get_logs()
        assert len(logs) == 0
        log = unify.log()
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].params == {"a": "a"}
        unify.add_log_params(logs=log, b="b", c="c")
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].params == {"a": "a", "b": "b", "c": "c"}
        with unify.Entries(d="d"):
            unify.add_log_entries(logs=log)
            logs = unify.get_logs()
            assert len(logs) == 1
            assert logs[0].entries == {"d": "d"}
            assert logs[0].params == {"a": "a", "b": "b", "c": "c"}
            unify.add_log_entries(logs=log, e="e")
            unify.add_log_params(logs=log, f="f")
            logs = unify.get_logs()
            assert len(logs) == 1
            assert logs[0].entries == {"d": "d", "e": "e"}
            assert logs[0].params == {
                "a": "a",
                "b": "b",
                "c": "c",
                "f": "f",
            }
            with unify.Log():
                unify.add_log_params(g="g")
                unify.add_log_entries(h="h")
                logs = unify.get_logs()
                assert len(logs) == 2
                assert logs[1].params == {"a": "a", "g": "g"}
                assert logs[1].entries == {"d": "d", "h": "h"}
            unify.add_log_entries(logs=log, i="i")
            logs = unify.get_logs()
            assert len(logs) == 2
            assert logs[0].entries == {"d": "d", "e": "e", "i": "i"}
            assert logs[0].params == {
                "a": "a",
                "b": "b",
                "c": "c",
                "f": "f",
            }


def test_with_all_threaded():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

    def fn(a, b, c, d, e, f, g, h, i):
        with unify.Params(a=a):
            log = unify.log()
            unify.add_log_params(logs=log, b=b, c=c)
            with unify.Entries(d=d):
                unify.add_log_entries(logs=log)
                unify.add_log_entries(logs=log, e=e)
                unify.add_log_params(logs=log, f=f)
                with unify.Log():
                    unify.add_log_params(g=g)
                    unify.add_log_entries(h=h)
                unify.add_log_entries(logs=log, i=i)

    threads = [
        threading.Thread(
            target=fn,
            args=[9 * i + j for j in range(9)],
        )
        for i in range(4)
    ]
    [t.start() for t in threads]
    [t.join() for t in threads]

    logs = unify.get_logs(project="my_project")

    params = [log.params for log in logs]
    observed = [sorted(d.items()) for d in sorted(params, key=lambda x: x["a"])]
    for i, obs in enumerate(observed):
        if i % 2 == 0:
            assert obs == [
                ("a", (i / 2) * 9),
                ("b", (i / 2) * 9 + 1),
                ("c", (i / 2) * 9 + 2),
                ("f", (i / 2) * 9 + 5),
            ]
        else:
            assert obs == [
                ("a", math.floor(i / 2) * 9),
                ("g", math.floor(i / 2) * 9 + 6),
            ]
    entries = [log.entries for log in logs]
    observed = [sorted(d.items()) for d in sorted(entries, key=lambda x: x["d"])]
    for i, obs in enumerate(observed):
        if i % 2 == 0:
            assert obs == [
                ("d", (i / 2) * 9 + 3),
                ("e", (i / 2) * 9 + 4),
                ("i", (i / 2) * 9 + 8),
            ]
        else:
            assert obs == [
                ("d", math.floor(i / 2) * 9 + 3),
                ("h", math.floor(i / 2) * 9 + 7),
            ]


@pytest.mark.asyncio
async def test_with_all_async():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

    async def fn(a, b, c, d, e, f, g, h, i):
        with unify.Params(a=a):
            log = unify.log()
            unify.add_log_params(logs=log, b=b, c=c)
            with unify.Entries(d=d):
                unify.add_log_entries(logs=log)
                unify.add_log_entries(logs=log, e=e)
                unify.add_log_params(logs=log, f=f)
                with unify.Log():
                    unify.add_log_params(g=g)
                    unify.add_log_entries(h=h)
                unify.add_log_entries(logs=log, i=i)

    fns = [fn(*[9 * i + j for j in range(9)]) for i in range(4)]
    await asyncio.gather(*fns)

    logs = unify.get_logs(project="my_project")

    params = [log.params for log in logs]
    observed = [sorted(d.items()) for d in sorted(params, key=lambda x: x["a"])]
    for i, obs in enumerate(observed):
        if i % 2 == 0:
            assert obs == [
                ("a", (i / 2) * 9),
                ("b", (i / 2) * 9 + 1),
                ("c", (i / 2) * 9 + 2),
                ("f", (i / 2) * 9 + 5),
            ]
        else:
            assert obs == [
                ("a", math.floor(i / 2) * 9),
                ("g", math.floor(i / 2) * 9 + 6),
            ]
    entries = [log.entries for log in logs]
    observed = [sorted(d.items()) for d in sorted(entries, key=lambda x: x["d"])]
    for i, obs in enumerate(observed):
        if i % 2 == 0:
            assert obs == [
                ("d", (i / 2) * 9 + 3),
                ("e", (i / 2) * 9 + 4),
                ("i", (i / 2) * 9 + 8),
            ]
        else:
            assert obs == [
                ("d", math.floor(i / 2) * 9 + 3),
                ("h", math.floor(i / 2) * 9 + 7),
            ]


# Trace #
# ------#


def test_traced():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

    @unify.traced
    def deeper_fn():
        time.sleep(1)
        return 3

    @unify.traced
    def inner_fn():
        time.sleep(1)
        deeper_fn()
        return 2

    @unify.traced
    def some_func(st):
        time.sleep(st)
        inner_fn()
        inner_fn()
        return 1

    some_func(0.5)
    entries = unify.get_logs(project="my_project")[0].entries

    assert entries["trace"]["inputs"] == {"st": 0.5}
    assert entries["trace"]["span_name"] == "some_func"
    assert (
        entries["trace"]["code"].replace(" ", "").replace("\n", "")
        == """
            @unify.traced
                def some_func(st):
                    time.sleep(st)
                    inner_fn()
                    inner_fn()
                    return 1
            """.replace(
            " ",
            "",
        ).replace(
            "\n",
            "",
        )
    )
    assert len(entries["trace"]["child_spans"]) == 2
    assert entries["trace"]["child_spans"][0]["span_name"] == "inner_fn"
    assert len(entries["trace"]["child_spans"][0]["child_spans"]) == 1
    assert (
        entries["trace"]["child_spans"][0]["child_spans"][0]["span_name"] == "deeper_fn"
    )


def test_traced_w_caching():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)
    if os.path.exists(".test_traced_w_cached.cache.json"):
        os.remove(".test_traced_w_cached.cache.json")
    unify.set_caching(True)
    unify.set_caching_fname(".test_traced_w_cached.cache.json")

    @unify.traced
    def some_func(a, b, c):
        return [a, b, c]

    some_func(0, 1, 2)
    logs = unify.get_logs(project="my_project")
    assert len(logs) == 1
    trace = logs[0].entries["trace"]
    idx = trace["id"]
    assert isinstance(idx, str)
    assert trace["span_name"] == "some_func"
    exec_time = trace["exec_time"]
    assert isinstance(exec_time, float)
    assert (
        trace["code"].replace(" ", "")
        == "@unify.traced\ndefsome_func(a,b,c):\nreturn[a,b,c]\n"
    )
    assert trace["inputs"] == {"a": 0, "b": 1, "c": 2}
    assert trace["outputs"] == [0, 1, 2]

    some_func(0, 1, 2)
    logs = unify.get_logs(project="my_project")
    assert len(logs) == 1
    trace = logs[0].entries["trace"]
    assert trace["id"] == idx
    assert trace["span_name"] == "some_func"
    assert trace["exec_time"] == exec_time
    assert (
        trace["code"].replace(" ", "")
        == "@unify.traced\ndefsome_func(a,b,c):\nreturn[a,b,c]\n"
    )
    assert trace["inputs"] == {"a": 0, "b": 1, "c": 2}
    assert trace["outputs"] == [0, 1, 2]


def test_traced_none_handling():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

    @unify.traced(prune_empty=False)
    def some_func(a, b, c, d):
        return [a, b, c, d]

    some_func(1, 2, None, 4)
    logs = unify.get_logs(project="my_project")
    assert len(logs) == 1
    entries = logs[0].entries
    assert entries["trace"]["inputs"] == {"a": 1, "b": 2, "c": None, "d": 4}
    assert entries["trace"]["span_name"] == "some_func"
    assert (
        entries["trace"]["code"].replace(" ", "").replace("\n", "")
        == """
            @unify.traced(prune_empty=False)
            def some_func(a, b, c, d):
                return [a, b, c, d]
            """.replace(
            " ",
            "",
        ).replace(
            "\n",
            "",
        )
    )
    assert len(entries["trace"]["child_spans"]) == 0

    @unify.traced(prune_empty=True)
    def some_func(a, b, c, d):
        return [a, b, c, d]

    some_func(1, 2, None, 4)
    logs = unify.get_logs(project="my_project")
    assert len(logs) == 2
    entries = logs[1].entries
    assert entries["trace"]["inputs"] == {"a": 1, "b": 2, "d": 4}
    assert entries["trace"]["span_name"] == "some_func"
    assert (
        entries["trace"]["code"].replace(" ", "").replace("\n", "")
        == """
            @unify.traced(prune_empty=True)
            def some_func(a, b, c, d):
                return [a, b, c, d]
            """.replace(
            " ",
            "",
        ).replace(
            "\n",
            "",
        )
    )
    assert "child_spans" not in entries["trace"]


def test_traced_within_log_context():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

    @unify.traced
    def deeper_fn():
        time.sleep(1)
        return 3

    @unify.traced
    def inner_fn():
        time.sleep(1)
        deeper_fn()
        return 2

    @unify.traced
    def some_func(st):
        time.sleep(st)
        inner_fn()
        inner_fn()
        return 1

    with unify.Log(a="a", b="b"):
        some_func(0.5)
    logs = unify.get_logs(project="my_project")
    assert len(logs) == 1
    entries = logs[0].entries
    assert entries["a"] == "a"
    assert entries["b"] == "b"
    assert entries["trace"]["inputs"] == {"st": 0.5}
    assert entries["trace"]["span_name"] == "some_func"
    assert len(entries["trace"]["child_spans"]) == 2
    assert entries["trace"]["child_spans"][0]["span_name"] == "inner_fn"
    assert len(entries["trace"]["child_spans"][0]["child_spans"]) == 1
    assert (
        entries["trace"]["child_spans"][0]["child_spans"][0]["span_name"] == "deeper_fn"
    )


def test_traced_threaded():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

    @unify.traced
    def deeper_fn():
        time.sleep(1)
        return 3

    @unify.traced
    def inner_fn():
        time.sleep(1)
        deeper_fn()
        return 2

    @unify.traced
    def some_func(st):
        time.sleep(st)
        inner_fn()
        inner_fn()
        return 1

    threads = [
        threading.Thread(
            target=some_func,
            args=[i / 100],
        )
        for i in range(8)
    ]
    [t.start() for t in threads]
    [t.join() for t in threads]

    logs = unify.get_logs(project="my_project")

    for i, log in enumerate(logs):
        trace = log.entries["trace"]
        assert trace["inputs"] == {"st": i / 100}
        assert trace["span_name"] == "some_func"
        assert len(trace["child_spans"]) == 2
        assert trace["child_spans"][0]["span_name"] == "inner_fn"
        assert len(trace["child_spans"][0]["child_spans"]) == 1
        assert trace["child_spans"][0]["child_spans"][0]["span_name"] == "deeper_fn"


@pytest.mark.asyncio
async def test_traced_async():
    project = "my_project"
    if project in unify.list_projects():
        unify.delete_project(project)
    unify.create_project(project)
    unify.activate(project)

    @unify.traced
    async def deeper_fn():
        time.sleep(1)
        return 3

    @unify.traced
    async def inner_fn():
        time.sleep(1)
        await deeper_fn()
        return 2

    @unify.traced
    async def some_func(st):
        time.sleep(st)
        await inner_fn()
        await inner_fn()
        return 1

    await asyncio.gather(*[some_func(i / 100) for i in range(8)])

    logs = unify.get_logs(project="my_project")

    for i, log in enumerate(logs):
        trace = log.entries["trace"]
        assert trace["inputs"] == {"st": i / 100}
        assert trace["span_name"] == "some_func"
        assert len(trace["child_spans"]) == 2
        assert trace["child_spans"][0]["span_name"] == "inner_fn"
        assert len(trace["child_spans"][0]["child_spans"]) == 1
        assert trace["child_spans"][0]["child_spans"][0]["span_name"] == "deeper_fn"


if __name__ == "__main__":
    pass
