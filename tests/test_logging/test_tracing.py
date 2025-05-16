import asyncio
import importlib
import inspect
import sys
import threading
import time

import pytest
import unify
from unify.logging.utils.logs import _get_trace_logger

from .helpers import _handle_project

# Trace #
# ------#


def _wait_for_trace_logger():
    while _get_trace_logger().queue.qsize() > 0:
        time.sleep(0.1)


@_handle_project
def test_traced():
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
    _wait_for_trace_logger()
    entries = unify.get_logs()[0].entries

    assert entries["trace"]["inputs"] == {"st": 0.5}
    assert entries["trace"]["span_name"] == "some_func"
    assert (
        entries["trace"]["code"].replace(" ", "").replace("\n", "")
        == """```python
            @unify.traced
                def some_func(st):
                    time.sleep(st)
                    inner_fn()
                    inner_fn()
                    return 1
            ```""".replace(
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


@_handle_project
def test_traced_w_arg_naming():

    @unify.traced(name="some_func_{arg}")
    def some_func(arg):
        return arg + 1

    some_func(1)
    _wait_for_trace_logger()
    entries = unify.get_logs()[0].entries

    assert entries["trace"]["inputs"] == {"arg": 1}
    assert entries["trace"]["span_name"] == "some_func_1"


@_handle_project
def test_traced_w_exception():
    @unify.traced
    def deeper_fn(inp):
        if inp == 2:
            raise ValueError("Something went wrong")
        return 3

    @unify.traced
    def inner_fn(inp):
        deeper_fn(inp)
        return 2

    @unify.traced
    def some_func(inp):
        inner_fn(inp)
        inner_fn(inp + 1)
        return 1

    try:
        some_func(1)
    except ValueError:
        pass
    _wait_for_trace_logger()
    trace = unify.get_logs()[0].entries["trace"]

    assert trace["inputs"] == {"inp": 1}
    assert trace["span_name"] == "some_func"
    assert (
        trace["code"].replace(" ", "").replace("\n", "")
        == """```python
            @unify.traced
                def some_func(inp):
                    inner_fn(inp)
                    inner_fn(inp+1)
                    return 1
            ```""".replace(
            " ",
            "",
        ).replace(
            "\n",
            "",
        )
    )
    assert len(trace["child_spans"]) == 2
    assert trace["child_spans"][0]["span_name"] == "inner_fn"
    assert len(trace["child_spans"][0]["child_spans"]) == 1
    assert trace["child_spans"][0]["child_spans"][0]["span_name"] == "deeper_fn"
    assert "Something went wrong" in trace["child_spans"][1]["child_spans"][0]["errors"]


@_handle_project
def test_traced_uni_llm():

    client = unify.Unify("gpt-4o@openai", traced=True)
    client.generate("hello")
    _wait_for_trace_logger()
    trace = unify.get_logs()[0].entries["trace"]

    assert trace["type"] == "llm"
    assert trace["span_name"] == "gpt-4o@openai"
    assert trace["offset"] == 0
    assert trace["inputs"] == {
        "messages": [{"role": "user", "content": "hello"}],
        "model": "gpt-4o@openai",
        "stream": False,
        "temperature": 1.0,
        "extra_body": {
            "signature": "python",
            "use_custom_keys": False,
            "drop_params": True,
            "log_query_body": True,
            "log_response_body": True,
        },
    }
    outputs = trace["outputs"]
    choices = outputs["choices"]
    assert len(choices) == 1
    choice = choices[0]
    assert choice["finish_reason"] == "stop"
    assert choice["index"] == 0
    message = choice["message"]
    assert message["role"] == "assistant"
    assert outputs["model"] == "gpt-4o@openai"
    assert outputs["object"] == "chat.completion"


@_handle_project
def test_traced_uni_llm_w_caching():

    client = unify.Unify("gpt-4o@openai", cache=True)
    client.generate("hello")
    client.set_traced(True)
    client.generate("hello")
    _wait_for_trace_logger()
    trace = unify.get_logs()[0].entries["trace"]

    assert trace["type"] == "llm-cached"
    assert trace["span_name"] == "gpt-4o@openai"
    assert trace["offset"] == 0
    assert trace["inputs"] == {
        "messages": [{"role": "user", "content": "hello"}],
        "model": "gpt-4o@openai",
        "stream": False,
        "temperature": 1.0,
        "extra_body": {
            "signature": "python",
            "use_custom_keys": False,
            "drop_params": True,
            "log_query_body": True,
            "log_response_body": True,
        },
    }
    outputs = trace["outputs"]
    choices = outputs["choices"]
    assert len(choices) == 1
    choice = choices[0]
    assert choice["finish_reason"] == "stop"
    assert choice["index"] == 0
    message = choice["message"]
    assert message["role"] == "assistant"
    assert outputs["model"] == "gpt-4o@openai"
    assert outputs["object"] == "chat.completion"


@_handle_project
def test_traced_none_handling():
    @unify.traced(prune_empty=False)
    def some_func(a, b, c, d):
        return [a, b, c, d]

    some_func(1, 2, None, 4)
    _wait_for_trace_logger()
    logs = unify.get_logs()
    assert len(logs) == 1
    entries = logs[0].entries
    assert entries["trace"]["inputs"] == {"a": 1, "b": 2, "c": None, "d": 4}
    assert entries["trace"]["span_name"] == "some_func"
    assert (
        entries["trace"]["code"].replace(" ", "").replace("\n", "")
        == """```python
            @unify.traced(prune_empty=False)
            def some_func(a, b, c, d):
                return [a, b, c, d]
            ```""".replace(
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
    _wait_for_trace_logger()
    logs = unify.get_logs()
    assert len(logs) == 2
    entries = logs[0].entries
    assert entries["trace"]["inputs"] == {"a": 1, "b": 2, "d": 4}
    assert entries["trace"]["span_name"] == "some_func"
    assert (
        entries["trace"]["code"].replace(" ", "").replace("\n", "")
        == """```python
            @unify.traced(prune_empty=True)
            def some_func(a, b, c, d):
                return [a, b, c, d]
            ```""".replace(
            " ",
            "",
        ).replace(
            "\n",
            "",
        )
    )
    assert "child_spans" not in entries["trace"]


@_handle_project
def test_traced_within_log_context():
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
    _wait_for_trace_logger()
    logs = unify.get_logs()
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


@_handle_project
def test_traced_threaded():
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

    _wait_for_trace_logger()
    logs = unify.get_logs()

    for i, log in enumerate(logs):
        trace = log.entries["trace"]
        assert trace["inputs"] == {"st": (7 - i) / 100}
        assert trace["span_name"] == "some_func"
        assert len(trace["child_spans"]) == 2
        assert trace["child_spans"][0]["span_name"] == "inner_fn"
        assert len(trace["child_spans"][0]["child_spans"]) == 1
        assert trace["child_spans"][0]["child_spans"][0]["span_name"] == "deeper_fn"


@_handle_project
@pytest.mark.asyncio
async def test_traced_async():
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

    _wait_for_trace_logger()
    logs = unify.get_logs()

    for i, log in enumerate(logs):
        trace = log.entries["trace"]
        assert trace["inputs"] == {"st": i / 100}
        assert trace["span_name"] == "some_func"
        assert len(trace["child_spans"]) == 2
        assert trace["child_spans"][0]["span_name"] == "inner_fn"
        assert len(trace["child_spans"][0]["child_spans"]) == 1
        assert trace["child_spans"][0]["child_spans"][0]["span_name"] == "deeper_fn"


@_handle_project
@pytest.mark.asyncio
async def test_traced_async_within_log_context():
    @unify.traced
    async def deeper_fn():
        return 3

    @unify.traced
    async def inner_fn():
        await deeper_fn()
        return 2

    @unify.traced
    async def some_func():
        await inner_fn()
        await inner_fn()
        return 1

    with unify.Log(a="a", b="b"):
        await some_func()

    _wait_for_trace_logger()
    logs = unify.get_logs()

    assert len(logs) == 1
    entries = logs[0].entries
    assert entries["a"] == "a"
    assert entries["b"] == "b"
    assert entries["trace"]["span_name"] == "some_func"
    assert len(entries["trace"]["child_spans"]) == 2
    assert entries["trace"]["child_spans"][0]["span_name"] == "inner_fn"
    assert len(entries["trace"]["child_spans"][0]["child_spans"]) == 1
    assert (
        entries["trace"]["child_spans"][0]["child_spans"][0]["span_name"] == "deeper_fn"
    )


@_handle_project
@pytest.mark.asyncio
async def test_traced_async_source_code():
    @unify.traced
    async def some_func(a, b):
        c = a + b
        return c

    await some_func(1, 2)
    _wait_for_trace_logger()
    logs = unify.get_logs()
    assert len(logs) == 1
    source = inspect.getsource(some_func).replace(" ", "").replace("\n", "")
    assert logs[0].entries["trace"]["code"].replace(" ", "").replace("\n", "") == source


@_handle_project
@pytest.mark.asyncio
async def test_traced_async_with_exception():
    @unify.traced
    async def some_func():
        raise ValueError("Something went wrong")

    try:
        await some_func()
    except ValueError:
        pass

    _wait_for_trace_logger()
    logs = unify.get_logs()
    assert len(logs) == 1
    assert "Something went wrong" in logs[0].entries["trace"]["errors"]


@_handle_project
def test_traced_class():
    @unify.traced
    class Foo:
        def __init__(self, a):
            self.a = a

        def add(self, b):
            return self.a + b

        def result(self):
            return self.a

    foo = Foo(0)
    foo.add(1)
    foo.result()

    _wait_for_trace_logger()
    logs = unify.get_logs()

    assert len(logs) == 2
    sorted_logs = sorted(logs, key=lambda x: x.entries["trace"]["span_name"])

    assert sorted_logs[0].entries["trace"]["span_name"] == "Foo.add"
    assert ["self", "b"] == list(sorted_logs[0].entries["trace"]["inputs"].keys())

    assert sorted_logs[0].entries["trace"]["inputs"]["b"] == 1
    assert sorted_logs[1].entries["trace"]["span_name"] == "Foo.result"
    assert ["self"] == list(sorted_logs[1].entries["trace"]["inputs"].keys())


@_handle_project
def test_traced_module():
    source_code = """
def add(a, b):
    return a + b

def sub(a, b):
    return a - b

class Foo:
    def __init__(self, a):
        self.a = a

    def add(self, b):
        return self.a + b

"""
    spec = importlib.util.spec_from_loader("test_module", loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(source_code, module.__dict__)
    unify.traced(module)
    module.add(1, 0)
    module.sub(1, 2)
    module.Foo(0).add(2)

    _wait_for_trace_logger()
    logs = list(reversed(unify.get_logs()))
    assert len(logs) == 3
    assert logs[0].entries["trace"]["span_name"] == "test_module.add"
    assert logs[0].entries["trace"]["inputs"] == {"a": 1, "b": 0}
    assert logs[0].entries["trace"]["outputs"] == 1

    assert logs[1].entries["trace"]["span_name"] == "test_module.sub"
    assert logs[1].entries["trace"]["inputs"] == {"a": 1, "b": 2}
    assert logs[1].entries["trace"]["outputs"] == -1

    assert logs[2].entries["trace"]["span_name"] == "test_module.Foo.add"


@_handle_project
def test_traced_install_and_disable_tracing_hook():
    from unify.logging.utils.tracing import TraceFinder

    unify.install_tracing_hook(["test_tracing_package"])
    assert any(isinstance(finder, TraceFinder) for finder in sys.meta_path)

    unify.disable_tracing_hook()
    assert not any(isinstance(finder, TraceFinder) for finder in sys.meta_path)


@_handle_project
def test_traced_install_tracing_hook(tmpdir):
    package_dir = tmpdir.join("test_tracing_package")
    package_dir.mkdir()

    with open(package_dir.join("__init__.py"), "w") as f:
        f.write("# Package initialization\n")
        f.write("from .module1 import add_abs\n")

    with open(package_dir.join("module1.py"), "w") as f:
        f.write(
            """
from .module2 import abs

def add_abs(a, b):
    return abs(a) + abs(b)
""",
        )

    with open(package_dir.join("module2.py"), "w") as f:
        f.write(
            """
def abs(a):
    return a if a > 0 else -a
""",
        )

    sys.path.insert(0, tmpdir.strpath)
    unify.install_tracing_hook(["test_tracing_package"])

    try:
        import test_tracing_package

        test_tracing_package.add_abs(-2, -3)

    finally:
        sys.path.remove(tmpdir.strpath)
        unify.disable_tracing_hook()

    _wait_for_trace_logger()
    logs = unify.get_logs()
    assert len(logs) == 1

    entry = logs[0].entries["trace"]
    assert entry["span_name"] == "test_tracing_package.module1.add_abs"
    assert entry["inputs"] == {"a": -2, "b": -3}
    assert entry["outputs"] == 5
    assert len(entry["child_spans"]) == 2
    assert entry["child_spans"][0]["span_name"] == "test_tracing_package.module2.abs"
    assert entry["child_spans"][1]["span_name"] == "test_tracing_package.module2.abs"


@_handle_project
def test_traced_context():
    unify.set_trace_context("Tracing")

    @unify.traced
    def some_func(arg):
        return arg + 1

    with unify.Context("Foo"):
        unify.log(a=1)

    [some_func(i) for i in range(5)]

    with unify.Context("Foo"):
        unify.log(a=2)

    _wait_for_trace_logger()
    logs = unify.get_logs(context="Foo")
    assert len(logs) == 2

    logs = unify.get_logs(context="Tracing")
    assert len(logs) == 5

    unify.set_trace_context(None)


@_handle_project
def test_traced_context_set_get():
    unify.set_trace_context("Tracing")
    assert unify.get_trace_context() == "Tracing"

    unify.set_trace_context(None)
    assert unify.get_trace_context() is None


if __name__ == "__main__":
    pass
