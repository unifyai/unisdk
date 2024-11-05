import time
import pytest
import asyncio

import unify


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
            t0 = time.perf_counter()
            unify.map(evaluate_w_log, qs)
            mapped_time = time.perf_counter() - t0
            t0 = time.perf_counter()
            for q in qs:
                evaluate_w_log(q)
            serial_time = time.perf_counter() - t0
            assert serial_time > 1.5 * mapped_time  # at least 2x faster


def test_threaded_map_with_context() -> None:
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
            )
            assert results == [1 + 3 + 2, 2 + 4 + 4]
            results = unify.map(
                contextual_func,
                (1, 2),
                (3, 4),
                c=(2, 4),
            )
            assert results == [1 + 3 + 2, 2 + 4 + 4]
            results = unify.map(
                contextual_func,
                (1, 3),
                b=(2, 4),
                c=(2, 4),
            )
            assert results == [1 + 2 + 2, 3 + 4 + 4]


def test_asyncio_map() -> None:
    t0 = time.perf_counter()
    unify.map(async_evaluate, qs, mode="asyncio")
    mapped_time = time.perf_counter() - t0
    t0 = time.perf_counter()
    for q in qs:
        evaluate(q)
    serial_time = time.perf_counter() - t0
    assert serial_time > 1.5 * mapped_time  # at least 2x faster


@pytest.mark.asyncio
def test_asyncio_map_with_context() -> None:
    with ProjectHandling():
        with unify.Project("test_project"):

            async def contextual_func(a, b, c=3):
                with unify.Entries(a=a, b=b, c=c):
                    await asyncio.sleep(0.1)
                    unify.log(test="some random value")
                return a + b + c

            results = unify.map(
                contextual_func,
                (1, 2),
                (3, 4),
                c=2,
                mode="asyncio",
            )
            assert results == [1 + 3 + 2, 2 + 4 + 2]
            results = unify.map(
                contextual_func,
                (1, 2),
                (3, 4),
                c=[2, 4],
                mode="asyncio",
            )
            assert results == [1 + 3 + 2, 2 + 4 + 4]
            results = unify.map(
                contextual_func,
                (1, 3),
                b=[2, 4],
                c=[2, 4],
                mode="asyncio",
            )
            assert results == [1 + 2 + 2, 3 + 4 + 4]


if __name__ == "__main__":
    pass
