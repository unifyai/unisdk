import random
import time

import pytest
import unify
from tests.test_utils.helpers import _CacheHandler
from unify.utils._caching import _get_cache, _write_to_cache

from ..test_logging.helpers import _handle_project

# Helpers #
# --------#


class ProjectHandling:
    def __enter__(self):
        if "test_project" in unify.list_projects():
            unify.delete_project("test_project")

    def __exit__(self, exc_type, exc_value, tb):
        if "test_project" in unify.list_projects():
            unify.delete_project("test_project")


client = unify.Unify("gpt-4o@openai", cache=True)
async_client = unify.AsyncUnify("gpt-4o@openai", cache=True)
qs = ["3 - 1", "4 + 7", "6 + 2", "9 - 3", "7 + 9"]


def evaluate_response(question: str, response: str) -> float:
    correct_answer = eval(question)
    try:
        response_int = int(
            "".join([c for c in response.split(" ")[-1] if c.isdigit()]),
        )
        return float(correct_answer == response_int)
    except ValueError:
        return 0.0


def evaluate(q: str):
    response = client.generate(q)
    evaluate_response(q, response)


def evaluate_w_log(q: str):
    response = client.generate(q)
    score = evaluate_response(q, response)
    return unify.log(
        question=q,
        response=response,
        score=score,
        skip_duplicates=False,
    )


@pytest.mark.asyncio
async def async_evaluate(q: str):
    response = await async_client.generate(q)
    return evaluate_response(q, response)


# Tests #
# ------#


def test_threaded_map() -> None:
    with ProjectHandling():
        with unify.Project("test_project"):
            unify.map(evaluate_w_log, qs)
            for q in qs:
                evaluate_w_log(q)


def test_map_mode() -> None:
    unify.set_map_mode("threading")
    assert unify.get_map_mode() == "threading"
    unify.map(evaluate_w_log, qs)
    unify.set_map_mode("asyncio")
    assert unify.get_map_mode() == "asyncio"
    unify.map(evaluate_w_log, qs)
    unify.set_map_mode("loop")
    assert unify.get_map_mode() == "loop"
    unify.map(evaluate_w_log, qs)


@_handle_project
def test_map_w_cache() -> None:
    with _CacheHandler():

        @unify.traced(name="gen{x}")
        def gen(x, cache):
            ret = None
            if cache in [True, "read", "read-only"]:
                ret = _get_cache(
                    fn_name="gen",
                    kw={"x": x},
                    raise_on_empty=(cache == "read-only"),
                )
            if ret is None:
                ret = random.randint(1, 5) + x
            if cache in [True, "write"]:
                _write_to_cache(
                    fn_name="gen",
                    kw={"x": x},
                    response=ret,
                )
            return ret

        @unify.traced
        def fn(cache):
            x = gen(0, cache)
            time.sleep(random.uniform(0, 0.1))
            y = gen(x, cache)
            time.sleep(random.uniform(0, 0.1))
            z = gen(y, cache)

        @unify.traced
        def cache_is_true():
            unify.map(fn, [True] * 10)

        @unify.traced
        def cache_is_read_only():
            unify.map(fn, ["read-only"] * 10)

        cache_is_true()
        cache_is_read_only()


def test_threaded_map_from_args() -> None:
    with ProjectHandling():
        with unify.Project("test_project"):
            unify.map(evaluate_w_log, qs, from_args=True)
            for q in qs:
                evaluate_w_log(q)


def test_threaded_map_with_context() -> None:
    with ProjectHandling():
        with unify.Project("test_project"):

            def contextual_func(a, b, c=3):
                with unify.Entries(a=a, b=b, c=c):
                    unify.log(test="some random value")
                return a + b + c

            results = unify.map(
                contextual_func,
                [
                    ((1, 3), {"c": 2}),
                    ((2, 4), {"c": 4}),
                ],
            )
            assert results == [1 + 3 + 2, 2 + 4 + 4]
            results = unify.map(
                contextual_func,
                [
                    ((1,), {"b": 2, "c": 2}),
                    ((3,), {"b": 4, "c": 4}),
                ],
            )
            assert results == [1 + 2 + 2, 3 + 4 + 4]


def test_threaded_map_with_context_from_args() -> None:
    with ProjectHandling():
        with unify.Project("test_project"):

            def contextual_func(a, b, c=3):
                with unify.Entries(a=a, b=b, c=c):
                    unify.log(test="some random value")
                return a + b + c

            results = unify.map(
                contextual_func,
                (1, 2),
                (3, 4),
                c=(2, 4),
                from_args=True,
            )
            assert results == [1 + 3 + 2, 2 + 4 + 4]
            results = unify.map(
                contextual_func,
                (1, 3),
                b=(2, 4),
                c=(2, 4),
                from_args=True,
            )
            assert results == [1 + 2 + 2, 3 + 4 + 4]


def test_asyncio_map() -> None:
    unify.map(async_evaluate, qs, mode="asyncio")
    for q in qs:
        evaluate(q)


def test_asyncio_map_from_args() -> None:
    unify.map(async_evaluate, qs, mode="asyncio", from_args=True)
    for q in qs:
        evaluate(q)


def test_loop_map() -> None:
    unify.map(evaluate_w_log, qs, mode="loop")


def test_loop_map_from_args() -> None:
    unify.map(evaluate_w_log, qs, mode="loop", from_args=True)


@pytest.mark.asyncio
def test_asyncio_map_with_context() -> None:
    with ProjectHandling():
        with unify.Project("test_project"):

            def contextual_func(a, b, c=3):
                with unify.Entries(a=a, b=b, c=c):
                    time.sleep(0.1)
                    unify.log(test="some random value")
                return a + b + c

            results = unify.map(
                contextual_func,
                [
                    ((1, 3), {"c": 2}),
                    ((2, 4), {"c": 4}),
                ],
                mode="asyncio",
            )
            assert results == [1 + 3 + 2, 2 + 4 + 4]
            results = unify.map(
                contextual_func,
                [
                    ((1,), {"b": 2, "c": 2}),
                    ((3,), {"b": 4, "c": 4}),
                ],
                mode="asyncio",
            )
            assert results == [1 + 2 + 2, 3 + 4 + 4]


@pytest.mark.asyncio
def test_asyncio_map_with_context_from_args() -> None:
    with ProjectHandling():
        with unify.Project("test_project"):

            def contextual_func(a, b, c=3):
                with unify.Entries(a=a, b=b, c=c):
                    time.sleep(0.1)
                    unify.log(test="some random value")
                return a + b + c

            results = unify.map(
                contextual_func,
                (1, 2),
                (3, 4),
                c=2,
                mode="asyncio",
                from_args=True,
            )
            assert results == [1 + 3 + 2, 2 + 4 + 2]
            results = unify.map(
                contextual_func,
                (1, 2),
                (3, 4),
                c=[2, 4],
                mode="asyncio",
                from_args=True,
            )
            assert results == [1 + 3 + 2, 2 + 4 + 4]
            results = unify.map(
                contextual_func,
                (1, 3),
                b=[2, 4],
                c=[2, 4],
                mode="asyncio",
                from_args=True,
            )
            assert results == [1 + 2 + 2, 3 + 4 + 4]


if __name__ == "__main__":
    pass
