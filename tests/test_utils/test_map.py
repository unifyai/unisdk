import time
import unittest
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


# Tests #
# ------#


class TestMap(unittest.TestCase):

    def setUp(self):
        self._client = unify.Unify("gpt-4o@openai")
        self._async_client = unify.AsyncUnify("gpt-4o@openai")
        self._qs = ["3 - 1", "4 + 7", "6 + 2", "9 - 3", "7 + 9"]

    @staticmethod
    def _evaluate_response(question: str, response: str) -> float:
        correct_answer = eval(question)
        try:
            response_int = int(
                "".join([c for c in response.split(" ")[-1] if c.isdigit()]),
            )
            return float(correct_answer == response_int)
        except ValueError:
            return 0.0

    def _evaluate(self, q: str):
        response = self._client.generate(q)
        self._evaluate_response(q, response)

    def _evaluate_w_log(self, q: str):
        response = self._client.generate(q)
        score = self._evaluate_response(q, response)
        return unify.log(
            question=q,
            response=response,
            score=score,
            skip_duplicates=False,
        )

    async def _async_evaluate(self, q: str):
        response = await self._async_client.generate(q)
        return self._evaluate_response(q, response)

    def test_threaded_map(self) -> None:
        with ProjectHandling():
            with unify.Project("test_project"):
                t0 = time.perf_counter()
                unify.map(self._evaluate_w_log, self._qs)
                mapped_time = time.perf_counter() - t0
                t0 = time.perf_counter()
                for q in self._qs:
                    self._evaluate_w_log(q)
                serial_time = time.perf_counter() - t0
                assert serial_time > 2 * mapped_time  # at least than 2x faster

    def test_threaded_map_with_context(self) -> None:
        with ProjectHandling():
            with unify.Project("test_project"):

                def contextual_func(a, b, c=3):
                    with unify.Entries(a=a, b=b, c=c):
                        unify.log(test="some random value")
                    return a + b + c

                results = unify.map(
                    contextual_func,
                    args=[(1, 2), (3, 4)],
                    kwargs={"c": 2},
                )
                assert results == [1 + 2 + 2, 3 + 4 + 2]
                results = unify.map(
                    contextual_func,
                    args=[(1, 2), (3, 4)],
                    kwargs=[{"c": 2}, {"c": 4}],
                )
                assert results == [1 + 2 + 2, 3 + 4 + 4]
                results = unify.map(
                    contextual_func,
                    args=[1, 3],
                    kwargs=[{"b": 2, "c": 2}, {"b": 4, "c": 4}],
                )
                assert results == [1 + 2 + 2, 3 + 4 + 4]

    def test_asyncio_map(self) -> None:
        t0 = time.perf_counter()
        unify.map(self._async_evaluate, self._qs, mode="asyncio")
        mapped_time = time.perf_counter() - t0
        t0 = time.perf_counter()
        for q in self._qs:
            self._evaluate(q)
        serial_time = time.perf_counter() - t0
        assert serial_time > 2 * mapped_time  # at least than 2x faster

    def test_asyncio_map_with_context(self) -> None:
        with ProjectHandling():
            with unify.Project("test_project"):

                async def contextual_func(a, b, c=3):
                    with unify.Entries(a=a, b=b, c=c):
                        await asyncio.sleep(0.1)
                        unify.log(test="some random value")
                    return a + b + c

                results = unify.map(
                    contextual_func,
                    args=[(1, 2), (3, 4)],
                    kwargs={"c": 2},
                    mode="asyncio",
                )
                assert results == [1 + 2 + 2, 3 + 4 + 2]
                results = unify.map(
                    contextual_func,
                    args=[(1, 2), (3, 4)],
                    kwargs=[{"c": 2}, {"c": 4}],
                    mode="asyncio",
                )
                assert results == [1 + 2 + 2, 3 + 4 + 4]
                results = unify.map(
                    contextual_func,
                    args=[1, 3],
                    kwargs=[{"b": 2, "c": 2}, {"b": 4, "c": 4}],
                    mode="asyncio",
                )
                assert results == [1 + 2 + 2, 3 + 4 + 4]
