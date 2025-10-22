import asyncio
import math
import threading

import pytest
import unify

from .helpers import _handle_project

# Functional Compositions #
# ------------------------#


@_handle_project
def test_get_param_by_version():
    unify.log(params={"sys_msg": "you are a helpful assistant"})
    unify.log(params={"sys_msg": "you are a very helpful assistant"})
    unify.log(params={"sys_msg": "you are a genious assistant"})
    assert unify.get_param_by_version("sys_msg", 0) == "you are a helpful assistant"
    assert (
        unify.get_param_by_version("sys_msg", 1) == "you are a very helpful assistant"
    )
    assert unify.get_param_by_version("sys_msg", 2) == "you are a genious assistant"


@_handle_project
def test_get_param_by_value():
    unify.log(params={"sys_msg": "you are a helpful assistant"})
    unify.log(params={"sys_msg": "you are a very helpful assistant"})
    unify.log(params={"sys_msg": "you are a genious assistant"})
    assert unify.get_param_by_value("sys_msg", "you are a helpful assistant") == "0"
    assert (
        unify.get_param_by_value("sys_msg", "you are a very helpful assistant") == "1"
    )
    assert unify.get_param_by_value("sys_msg", "you are a genious assistant") == "2"


@_handle_project
def test_get_experiment_name():
    unify.log(params={"experiment": "first_try"}, x=0)
    unify.log(params={"experiment": "second_try"}, x=1)
    unify.log(params={"experiment": "third_try"}, x=2)
    assert unify.get_experiment_name(-1) == "third_try"
    assert unify.get_experiment_name(-2) == "second_try"
    assert unify.get_experiment_name(-3) == "first_try"
    assert unify.get_experiment_name(0) == "first_try"
    assert unify.get_experiment_name(1) == "second_try"
    assert unify.get_experiment_name(2) == "third_try"


@_handle_project
def test_get_experiment_version():
    unify.log(params={"experiment": "first_try"}, x=0)
    unify.log(params={"experiment": "second_try"}, x=1)
    unify.log(params={"experiment": "third_try"}, x=2)
    assert unify.get_experiment_version("third_try") == 2
    assert unify.get_experiment_version("second_try") == 1
    assert unify.get_experiment_version("first_try") == 0


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
def test_with_context():
    [unify.log(x=i) for i in range(3)]

    with unify.Context("Foo", mode="both"):
        [unify.log(x=i) for i in range(10)]
        assert len(unify.get_logs()) == 10

    with unify.Context("Foo", mode="read"):
        assert len(unify.get_logs()) == 10

    with unify.Context("Foo", mode="write"):
        [unify.log(x=i) for i in range(10)]
        assert len(unify.get_logs()) == 3

    with unify.Context("Foo", mode="read"):
        assert len(unify.get_logs()) == 20

    with unify.Context("Foo"):
        assert len(unify.get_logs()) == 20


@_handle_project
def test_with_context_overwrite():
    with unify.Context("foo", overwrite=True):
        [unify.log(a=i) for i in range(10)]
        assert len(unify.get_logs()) == 10

    with unify.Context("foo"):
        assert len(unify.get_logs()) == 10
        [unify.log(a=i) for i in range(10)]

    with unify.Context("foo", overwrite=False):
        assert len(unify.get_logs()) == 20

    assert len(unify.get_logs(context="foo")) == 20

    with unify.Context("foo", overwrite=True):
        assert len(unify.get_logs()) == 0
        [unify.log(a=i) for i in range(10)]
        assert len(unify.get_logs()) == 10

    assert len(unify.get_logs(context="foo")) == 10


@_handle_project
def test_with_context_nested():

    with unify.Context("Foo"):
        [unify.log(x=i) for i in range(10)]

        with unify.Context("Bar"):
            [unify.log(y=i) for i in range(5)]
            assert len(unify.get_logs()) == 5

        with unify.Context("Bar/Baz"):
            [unify.log(z=i) for i in range(20)]
            assert len(unify.get_logs()) == 20

        with unify.Context("Bar"):
            with unify.Context("Baz"):
                assert len(unify.get_logs()) == 20

        assert len(unify.get_logs()) == 10


@_handle_project
def test_with_context_mode_nested():

    with unify.Context("Foo"):
        [unify.log(x=i) for i in range(10)]

        with unify.Context("Bar"):
            [unify.log(y=i) for i in range(5)]
            assert len(unify.get_logs()) == 5

        with unify.Context("Bar/Baz"):
            [unify.log(z=i) for i in range(20)]
            assert len(unify.get_logs()) == 20

        with unify.Context("Bar/Baz", mode="write"):
            [unify.log(y=i) for i in range(5)]
            assert len(unify.get_logs()) == 10  # Get from Foo

        with unify.Context("Bar/Baz", mode="read"):
            [unify.log(y=i) for i in range(5)]
            assert len(unify.get_logs()) == 25  # Read from Bar/Baz

        assert len(unify.get_logs()) == 15


@_handle_project
def test_with_context_mode_restricted():
    with unify.Context("Foo", mode="read"):
        with pytest.raises(Exception):
            with unify.Context("Bar", mode="write"):
                pass

    with unify.Context("Foo", mode="read"):
        with pytest.raises(Exception):
            with unify.Context("Bar", mode="both"):
                pass

    with unify.Context("Foo", mode="write"):
        with pytest.raises(Exception):
            with unify.Context("Bar", mode="both"):
                pass

    with unify.Context("Foo", mode="write"):
        with pytest.raises(Exception):
            with unify.Context("Bar", mode="read"):
                pass


@_handle_project
def test_with_context_threaded():
    NUM_THREADS = 4
    THREAD_MULTIPLIER = 10
    FOO_LOGS_PER_THREAD = 3
    BAR_LOGS_PER_THREAD = 5
    BAZ_LOGS_PER_THREAD = 7

    # Ensure context created before threads are started
    # Otherwise, each thread may try to create the context at the same time
    unify.create_context("Foo")
    unify.create_context("Foo/Bar")
    unify.create_context("Foo/Bar/Baz")

    def fn(i):
        with unify.Context("Foo"):
            [unify.log(x=j) for j in range(i, i + FOO_LOGS_PER_THREAD)]
            with unify.Context("Bar"):
                [unify.log(x=j) for j in range(i, i + BAR_LOGS_PER_THREAD)]
            with unify.Context("Bar/Baz"):
                [unify.log(x=j) for j in range(i, i + BAZ_LOGS_PER_THREAD)]

    threads = [
        threading.Thread(
            target=fn,
            args=[i * THREAD_MULTIPLIER],
        )
        for i in range(NUM_THREADS)
    ]
    [t.start() for t in threads]
    [t.join() for t in threads]

    with unify.Context("Foo"):
        assert len(unify.get_logs()) == NUM_THREADS * FOO_LOGS_PER_THREAD
        logs = unify.get_logs()
        x_values = sorted([log.entries["x"] for log in logs])
        expected_x = sorted(
            [
                j
                for i in range(NUM_THREADS)
                for j in range(
                    i * THREAD_MULTIPLIER,
                    i * THREAD_MULTIPLIER + FOO_LOGS_PER_THREAD,
                )
            ],
        )
        assert x_values == expected_x

    with unify.Context("Foo/Bar"):
        assert len(unify.get_logs()) == NUM_THREADS * BAR_LOGS_PER_THREAD
        logs = unify.get_logs()
        x_values = sorted([log.entries["x"] for log in logs])
        expected_x = sorted(
            [
                j
                for i in range(NUM_THREADS)
                for j in range(
                    i * THREAD_MULTIPLIER,
                    i * THREAD_MULTIPLIER + BAR_LOGS_PER_THREAD,
                )
            ],
        )
        assert x_values == expected_x

    with unify.Context("Foo/Bar/Baz"):
        assert len(unify.get_logs()) == NUM_THREADS * BAZ_LOGS_PER_THREAD
        logs = unify.get_logs()
        x_values = sorted([log.entries["x"] for log in logs])
        expected_x = sorted(
            [
                j
                for i in range(NUM_THREADS)
                for j in range(
                    i * THREAD_MULTIPLIER,
                    i * THREAD_MULTIPLIER + BAZ_LOGS_PER_THREAD,
                )
            ],
        )
        assert x_values == expected_x


# ToDo: add asyncio test


# Column Context


@_handle_project
@pytest.mark.skip(reason="Entries names are not handled properly from backend")
def test_with_column_context():

    unify.log(a="a")
    logs = unify.get_logs()
    assert len(logs) == 1
    assert logs[0].entries == {"a": "a"}
    with unify.ColumnContext("capitalized"):
        unify.log(a="a")
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].entries == {"a": "a"}
        unify.add_log_entries(logs=logs, b="B")
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].entries == {"a": "a", "capitalized/b": "B"}
        with unify.ColumnContext("vowels"):
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
                "capitalized/vowels/u": ("0", "U"),
            }
            unify.log(a="A")
    logs = unify.get_logs()
    assert len(logs) == 2
    assert logs[0].entries == {
        "capitalized/vowels/a": "A",
    }
    assert logs[1].entries == {
        "a": "a",
        "capitalized/b": "B",
        "capitalized/vowels/e": "E",
    }


@_handle_project
def test_with_col_context_get_logs():
    [unify.log(a=i) for i in range(10)]

    with unify.ColumnContext("foo"):
        [unify.log(a=i) for i in range(10)]
        assert len(unify.get_logs()) == 10

    with unify.ColumnContext("foo"):
        assert len(unify.get_logs()) == 10

    with unify.ColumnContext("foo/bar"):
        [unify.log(a=i) for i in range(10)]
        assert len(unify.get_logs()) == 10

    with unify.ColumnContext("foo"):
        assert len(unify.get_logs()) == 20

    assert len(unify.get_logs()) == 30


@_handle_project
def test_with_col_context_default_project():
    with unify.Log():
        with unify.ColumnContext("science"):
            with unify.ColumnContext("physics"):
                unify.log(score=1.0)
            with unify.ColumnContext("chemistry"):
                unify.log(score=0.5)
            with unify.ColumnContext("biology"):
                unify.log(score=0.0)

    entries = unify.get_logs()[0].entries
    assert entries["science/physics/score"] == 1.0
    assert entries["science/chemistry/score"] == 0.5
    assert entries["science/biology/score"] == 0.0


@_handle_project
def test_with_col_context_overwrite():
    with unify.ColumnContext("boo"):
        [unify.log(a=i) for i in range(10)]
        assert len(unify.get_logs()) == 10

    with unify.ColumnContext("foo"):
        [unify.log(a=i) for i in range(10)]
        assert len(unify.get_logs()) == 10

    with unify.ColumnContext("foo", overwrite=True):
        [unify.log(a=i) for i in range(5)]
        assert len(unify.get_logs()) == 5

    with unify.ColumnContext("foo", overwrite=False):
        assert len(unify.get_logs()) == 5
        [unify.log(a=i) for i in range(5)]

    assert len(unify.get_logs()) == 20


@_handle_project
def test_with_col_context_mode_restricted():
    with unify.ColumnContext("foo", mode="read"):
        with pytest.raises(Exception):
            with unify.ColumnContext("bar", mode="write"):
                pass

    with unify.ColumnContext("foo", mode="read"):
        with pytest.raises(Exception):
            with unify.ColumnContext("bar", mode="both"):
                pass

    with unify.ColumnContext("foo", mode="write"):
        with pytest.raises(Exception):
            with unify.ColumnContext("bar", mode="both"):
                pass

    with unify.ColumnContext("foo", mode="write"):
        with pytest.raises(Exception):
            with unify.ColumnContext("bar", mode="read"):
                pass


@_handle_project
def test_with_col_context_threaded():
    def fn(a, b, e):
        log = unify.log(a=a)
        with unify.ColumnContext("capitalized"):
            log.add_entries(b=b)
            with unify.ColumnContext("vowels"):
                log.add_entries(e=e)
                unify.log(a=a)

    threads = [
        threading.Thread(
            target=fn,
            args=[3 * i + j for j in range(3)],
        )
        for i in range(4)
    ]
    [t.start() for t in threads]
    [t.join() for t in threads]

    logs = reversed(unify.get_logs())
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


@_handle_project
@pytest.mark.asyncio
async def test_with_col_context_async():
    async def fn(a, b, e):
        log = unify.log(a=a)
        with unify.ColumnContext("capitalized"):
            log.add_entries(b=b)
            with unify.ColumnContext("vowels"):
                log.add_entries(e=e)
                unify.log(a=a)

    fns = [fn(*[3 * i + j for j in range(3)]) for i in range(4)]
    await asyncio.gather(*fns)

    logs = unify.get_logs()
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


@_handle_project
def test_with_entries():

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


@_handle_project
def test_with_entries_threaded():
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

    logs = unify.get_logs()
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


@_handle_project
@pytest.mark.asyncio
async def test_with_entries_async():
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

    logs = unify.get_logs()
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


@_handle_project
def test_with_entries_mode():
    with unify.Entries(x=0):
        unify.log(y=1)
        assert len(unify.get_logs()) == 1

    with unify.Entries(x=0, y=1, mode="read"):
        assert len(unify.get_logs()) == 1

    with unify.Entries(x=0, y=2, mode="write"):
        unify.log()
        assert len(unify.get_logs()) == 2

    with unify.Entries(x=1, y=3):
        assert len(unify.get_logs()) == 0
        [unify.log() for _ in range(2)]
        assert len(unify.get_logs()) == 2

    assert len(unify.get_logs()) == 4


@_handle_project
def test_with_entries_mode_restricted():
    with unify.Entries(x=0, mode="read"):
        with pytest.raises(Exception):
            with unify.Entries(x=0, mode="write"):
                pass

    with unify.Entries(x=0, mode="read"):
        with pytest.raises(Exception):
            with unify.Entries(x=0, mode="both"):
                pass

    with unify.Entries(msg="foo", mode="write"):
        with pytest.raises(Exception):
            with unify.Entries(msg="foo", mode="both"):
                pass

    with unify.Entries(msg="foo", mode="write"):
        with pytest.raises(Exception):
            with unify.Entries(msg="foo", mode="read"):
                pass


@_handle_project
def test_with_entries_overwrite():
    with unify.Entries(x=0):
        [unify.log(x=i) for i in range(20)]
        assert len(unify.get_logs()) == 20

    with unify.Entries(x=0, overwrite=True):
        [unify.log(x=i) for i in range(10)]
        assert len(unify.get_logs()) == 10

    assert len(unify.get_logs()) == 10

    with unify.Entries(x=0, overwrite=True):
        pass

    assert len(unify.get_logs()) == 0


# Params


@_handle_project
def test_with_params():

    with unify.Params(a="a"):
        logs = unify.get_logs()
        assert len(logs) == 0
        log = unify.log()
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].params == {"a": ("0", "a")}
        unify.add_log_params(logs=log, b="b", c="c")
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].params == {"a": ("0", "a"), "b": ("0", "b"), "c": ("0", "c")}
        with unify.Params(d="d"):
            unify.add_log_params(logs=log)
            logs = unify.get_logs()
            assert len(logs) == 1
            assert logs[0].params == {
                "a": ("0", "a"),
                "b": ("0", "b"),
                "c": ("0", "c"),
                "d": ("0", "d"),
            }
            unify.add_log_params(logs=log, e="e", f="f")
            logs = unify.get_logs()
            assert len(logs) == 1
            assert logs[0].params == {
                "a": ("0", "a"),
                "b": ("0", "b"),
                "c": ("0", "c"),
                "d": ("0", "d"),
                "e": ("0", "e"),
                "f": ("0", "f"),
            }
        unify.add_log_params(logs=log, g="g")
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].params == {
            "a": ("0", "a"),
            "b": ("0", "b"),
            "c": ("0", "c"),
            "d": ("0", "d"),
            "e": ("0", "e"),
            "f": ("0", "f"),
            "g": ("0", "g"),
        }


@_handle_project
def test_with_params_threaded():
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

    logs = reversed(unify.get_logs())
    params = [log.params for log in logs]

    assert sorted([sorted([(k, v[1]) for k, v in d.items()]) for d in params]) == [
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


@_handle_project
def test_with_params_mode():
    with unify.Params(msg="foo"):
        [unify.log(x=i) for i in range(10)]
        assert len(unify.get_logs()) == 10

    with unify.Params(msg="foo", mode="read"):
        assert len(unify.get_logs()) == 10

    with unify.Params(msg="foo"):
        with unify.Params(msg="bar"):
            [unify.log(x=i) for i in range(5)]
            assert len(unify.get_logs()) == 5

        with unify.Params(msg="bar", mode="write"):
            [unify.log(x=i) for i in range(5)]
            assert len(unify.get_logs()) == 10

        with unify.Params(msg="bar", mode="read"):
            [unify.log(x=i) for i in range(10)]
            assert len(unify.get_logs()) == 10

        assert len(unify.get_logs()) == 20

    assert len(unify.get_logs()) == 30


@_handle_project
def test_with_params_mode_multiple():
    with unify.Params(msg="foo"):
        [unify.log(x=i) for i in range(5)]
        assert len(unify.get_logs()) == 5

    with unify.Params(msg="foo", mode="read"):
        assert len(unify.get_logs()) == 5

    with unify.Params(msg="foo"):
        with unify.Params(reg="US"):
            [unify.log(x=i) for i in range(5)]
            assert len(unify.get_logs()) == 5

        with unify.Params(reg="US", mode="write"):
            [unify.log(x=i) for i in range(5)]
            assert len(unify.get_logs()) == 15

        with unify.Params(reg="US", mode="read"):
            assert len(unify.get_logs()) == 10
            [unify.log(x=i) for i in range(10)]

        assert len(unify.get_logs()) == 25

    assert len(unify.get_logs()) == 25


@_handle_project
def test_with_params_mode_restricted():
    with unify.Params(mode="read"):
        with pytest.raises(Exception):
            with unify.Params(mode="write"):
                pass

    with unify.Params(mode="read"):
        with pytest.raises(Exception):
            with unify.Params(mode="both"):
                pass

    with unify.Params(msg="foo", mode="write"):
        with pytest.raises(Exception):
            with unify.Params(msg="foo", mode="both"):
                pass

    with unify.Params(msg="foo", mode="write"):
        with pytest.raises(Exception):
            with unify.Params(msg="foo", mode="read"):
                pass


@_handle_project
def test_with_params_overwrite():
    with unify.Params(msg="foo"):
        [unify.log(x=i) for i in range(20)]
        assert len(unify.get_logs()) == 20

    with unify.Params(msg="foo", overwrite=True):
        [unify.log(x=i) for i in range(10)]
        assert len(unify.get_logs()) == 10

    assert len(unify.get_logs()) == 10

    with unify.Params(msg="foo", overwrite=True):
        pass

    assert len(unify.get_logs()) == 0


@_handle_project
@pytest.mark.asyncio
async def test_with_params_async():
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

    logs = unify.get_logs()
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


# Experiment


@_handle_project
def test_with_experiment():

    with unify.Experiment(), unify.Params(sys_msg="you are a helpful assistant"):
        unify.log(x=0)
        unify.log(x=1)
    assert unify.get_experiment_name(0) == "exp0"

    logs = unify.get_logs()[0:2]
    assert [lg.entries for lg in logs] == [{"x": 1}, {"x": 0}]

    with unify.Experiment(), unify.Params(
        sys_msg="you are a very helpful assistant",
    ):
        unify.log(x=1)
        unify.log(x=2)
    assert unify.get_experiment_name(0) == "exp0"
    assert unify.get_experiment_name(1) == "exp1"
    logs = unify.get_logs()[0:2]
    assert [lg.entries for lg in logs] == [{"x": 2}, {"x": 1}]

    with unify.Experiment("new_idea"), unify.Params(
        sys_msg="you are a genious assistant",
    ):
        unify.log(x=2)
        unify.log(x=3)
    assert unify.get_experiment_name(0) == "exp0"
    assert unify.get_experiment_name(1) == "exp1"
    assert unify.get_experiment_name(2) == "new_idea"
    logs = unify.get_logs()[0:2]
    assert [lg.entries for lg in logs] == [{"x": 3}, {"x": 2}]

    with unify.Experiment(-1, overwrite=True), unify.Params(
        sys_msg="you are a very helpful assistant",
    ):
        unify.log(x=3)
        unify.log(x=4)
    assert unify.get_experiment_name(0) == "exp0"
    assert unify.get_experiment_name(1) == "exp1"
    assert unify.get_experiment_name(2) == "new_idea"
    logs = unify.get_logs()[0:2]
    assert [lg.entries for lg in logs] == [{"x": 4}, {"x": 3}]


@_handle_project
def test_with_experiment_mode():
    with unify.Experiment("foo", mode="both"):
        [unify.log(x=i) for i in range(10)]
        assert len(unify.get_logs()) == 10

    with unify.Experiment("foo", mode="read"):
        assert len(unify.get_logs()) == 10

    with unify.Experiment("foo", mode="write"):
        [unify.log(x=i) for i in range(5)]
        assert len(unify.get_logs()) == 15

    with unify.Experiment("bar", mode="both"):
        [unify.log(x=i) for i in range(20)]
        assert len(unify.get_logs()) == 20
        with unify.Experiment("foo", mode="read"):
            assert len(unify.get_logs()) == 15

    assert len(unify.get_logs()) == 35


@_handle_project
def test_with_experiment_mode_restricted():
    with unify.Experiment(mode="read"):
        with pytest.raises(Exception):
            with unify.Experiment(mode="write"):
                pass

    with unify.Experiment(mode="read"):
        with pytest.raises(Exception):
            with unify.Experiment(mode="both"):
                pass

    with unify.Experiment("foo", mode="write"):
        with pytest.raises(Exception):
            with unify.Experiment("foo", mode="both"):
                pass

    with unify.Experiment("foo", mode="write"):
        with pytest.raises(Exception):
            with unify.Experiment(mode="read"):
                pass


# Combos


@_handle_project
def test_with_all():

    with unify.Params(a="a"):
        logs = unify.get_logs()
        assert len(logs) == 0
        log = unify.log()
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].params == {"a": ("0", "a")}
        unify.add_log_params(logs=log, b="b", c="c")
        logs = unify.get_logs()
        assert len(logs) == 1
        assert logs[0].params == {"a": ("0", "a"), "b": ("0", "b"), "c": ("0", "c")}
        with unify.Entries(d="d"):
            unify.add_log_entries(logs=log)
            logs = unify.get_logs()
            assert len(logs) == 1
            assert logs[0].entries == {"d": "d"}
            assert logs[0].params == {"a": ("0", "a"), "b": ("0", "b"), "c": ("0", "c")}
            unify.add_log_entries(logs=log, e="e")
            unify.add_log_params(logs=log, f="f")
            logs = unify.get_logs()
            assert len(logs) == 1
            assert logs[0].entries == {"d": "d", "e": "e"}
            assert logs[0].params == {
                "a": ("0", "a"),
                "b": ("0", "b"),
                "c": ("0", "c"),
                "f": ("0", "f"),
            }
            with unify.Log():
                unify.add_log_params(g="g")
                unify.add_log_entries(h="h")
                logs = unify.get_logs()
                assert len(logs) == 2
                assert logs[0].params == {"a": ("0", "a"), "g": ("0", "g")}
                assert logs[0].entries == {"d": "d", "h": "h"}
            unify.add_log_entries(logs=log, i="i")
            logs = unify.get_logs()
            assert len(logs) == 2
            assert logs[1].entries == {"d": "d", "e": "e", "i": "i"}
            assert logs[1].params == {
                "a": ("0", "a"),
                "b": ("0", "b"),
                "c": ("0", "c"),
                "f": ("0", "f"),
            }


@_handle_project
def test_with_all_threaded():
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

    logs = reversed(unify.get_logs())

    params = [log.params for log in logs]
    observed = [
        sorted([(k, v[1]) for k, v in d.items()])
        for d in sorted(params, key=lambda x: x["a"])
    ]
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


@_handle_project
@pytest.mark.asyncio
async def test_with_all_async():
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

    logs = unify.get_logs()

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


@_handle_project
def test_basic_log_decorator():
    @unify.log
    def sample_function(a, b, c, d):
        c = a + b
        d = c * 2
        return d

    sample_function(2, 3, 8, 9, w=2, y=9)
    logs = unify.get_logs()
    assert len(logs) == 1
    assert logs[0].entries == {
        "a": 2,
        "b": 3,
        "c": 5,
        "d": 10,
        "w": 2,
        "y": 9,
    }


@_handle_project
def test_log_decorator_w_internal_logging():
    @unify.log
    def sample_function(a, b, c, d):
        c = a + b
        unify.log(e=15)
        d = c * 2
        return d

    sample_function(2, 3, 8, 9, w=2, y=9)
    logs = unify.get_logs()
    assert len(logs) == 1
    assert logs[0].entries == {
        "e": 15,
        "a": 2,
        "b": 3,
        "c": 5,
        "d": 10,
        "w": 2,
        "y": 9,
    }


@_handle_project
def test_private_variable_exclusion():
    @unify.log
    def sample_function(public_var, _private_var):
        visible = public_var * 2
        _hidden = _private_var * 3
        result = visible + _hidden
        return result

    sample_function(5, 3)
    logs = unify.get_logs()
    assert len(logs) == 1
    # Verify public variables and computed results are captured
    assert "public_var" in logs[0].entries
    assert "visible" in logs[0].entries
    assert "result" in logs[0].entries
    # Ensure private variables are not present
    assert "_private_var" not in logs[0].entries
    assert "_hidden" not in logs[0].entries


@_handle_project
@pytest.mark.asyncio
async def test_async_log_decorator():
    @unify.log
    async def async_sample(x, y):
        z = x * y
        return z

    result = await async_sample(4, 5)
    logs = unify.get_logs()
    assert len(logs) == 1
    assert logs[0].entries == {
        "x": 4,
        "y": 5,
        "z": 20,
    }
    assert result == 20


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
