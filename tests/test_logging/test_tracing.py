import asyncio
import threading
import time

import pytest
import unify

from .helpers import _handle_project

# Trace #
# ------#


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
    assert trace["child_spans"][1]["child_spans"][0]["errors"] == "Something went wrong"


@_handle_project
def test_traced_uni_llm():

    client = unify.Unify("gpt-4o@openai", traced=True)
    client.generate("hello")
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

    logs = unify.get_logs()

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
