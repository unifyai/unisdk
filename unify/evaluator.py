import abc
from abc import abstractmethod
from typing import Type, Union

import unify.chat.clients

from unify.chat.clients import _Client
from unify.evaluation import Evaluation
from unify.types import Score, Datum, ChatCompletion


class Evaluator(abc.ABC):

    @property
    @abstractmethod
    def class_config(self) -> Type[Score]:
        raise NotImplemented

    @abstractmethod
    def _evaluate(
            self,
            datum: Datum,
            response: ChatCompletion,
    ) -> Union[bool, float, Score]:
        """
        Evaluate the given response for this datum.

        Args:
            datum: The datum (dataset entry) used for evaluation, containing an input
            prompt and optionally other extra data, such as a reference answer.

            response: The chat completion response which is being evaluated.
        """
        raise NotImplemented

    def evaluate(
            self,
            datum: Datum,
            response: ChatCompletion,
            agent: Union[str, _Client, unify.Agent]
    ):
        """
        Evaluate the given response for this datum.

        Args:
            datum: The datum (dataset entry) used for evaluation, containing an input
            prompt and optionally other extra data, such as a reference answer.

            response: The chat completion response which is being evaluated.

            agent: The agent for whom the evaluation is for.

        Returns:
            An Evaluation instance, containing the datum, response, agent and score.
        """
        score = self._evaluate(datum, response)
        if isinstance(score, bool):
            score = float(score)
        if isinstance(score, float):
            score = self.class_config(score)
        return Evaluation(
            datum=datum,
            response=response,
            agent=agent,
            score=score
        )
