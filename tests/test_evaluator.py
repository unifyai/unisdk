import unify
import unittest
from typing import Type, Dict


class TestEvaluators(unittest.TestCase):

    def setUp(self) -> None:
        self._system_msg = "Answer the following maths question, " \
                           "returning only the numeric answer, and nothing else."
        self._dataset = unify.Dataset(
            [unify.Prompt(q, system_message=self._system_msg) for q in
             ["1 + 3", "4 + 7", "6 + 5"]]
        )

        class Binary(unify.Score):

            @property
            def config(self) -> Dict[float, str]:
                return {
                    0.: "incorrect",
                    1.: "correct"
                }

        class MathsEvaluator(unify.Evaluator):

            @property
            def class_config(self) -> Type[unify.Score]:
                return Binary

            def _evaluate(self, prompt: str, response: str) -> bool:
                correct_answer = eval(prompt)
                try:
                    response_int = int(
                        "".join([c for c in response.split(" ")[-1] if c.isdigit()])
                    )
                    return correct_answer == response_int
                except ValueError:
                    return False

        self._evaluator = MathsEvaluator()
        self._client = unify.Unify("gpt-4o@openai", cache=True)

    def test_evals(self) -> None:
        for prompt in (unify.Datum("1 + 3"), unify.Prompt("1 + 3"), "1 + 3"):
            for response in (unify.ChatCompletion("4"), "4"):
                print(self._evaluator.evaluate(
                    prompt=prompt,
                    response=response,
                    agent=self._client
                ))
