import abc
from abc import abstractmethod
from typing import Type, Union
from openai.types.chat.chat_completion import ChatCompletionMessage, Choice

from unify.agent import Agent
from unify.chat.clients import _Client
from unify.evaluation import Evaluation
from unify.types import Score, Prompt, Datum, ChatCompletion


class Evaluator(abc.ABC):

    @property
    @abstractmethod
    def class_config(self) -> Type[Score]:
        raise NotImplemented

    @abstractmethod
    def _evaluate(
            self,
            datum: Union[Prompt, Datum],
            response: Union[ChatCompletion, str],
    ) -> Union[bool, float, Score]:
        """
        Evaluate the given response for this datum.

        Args:
            datum: The input prompt in isolation, or the datum (dataset entry),
            containing the input prompt and optionally other extra data, such as a
            reference answer.

            response: The chat completion response which is being evaluated, either as
            the full chat completion or just the most recent assistant message.
        """
        raise NotImplemented

    def evaluate(
            self,
            datum: Union[Prompt, Datum],
            response: Union[ChatCompletion, str],
            agent: Union[str, _Client, Agent]
    ):
        """
        Evaluate the given response for this datum.

        Args:
            datum: The input prompt in isolation, or the datum (dataset entry),
            containing the input prompt and optionally other extra data, such as a
            reference answer.

            response: The chat completion response which is being evaluated, either as
            the full chat completion or just the most recent assistant message.

            agent: The agent for whom the evaluation is for.

        Returns:
            An Evaluation instance, containing the datum, response, agent and score.
        """
        score = self._evaluate(datum, response)
        # handle datum
        if isinstance(datum, Prompt):
            datum = Datum(prompt=datum)
        # handle response
        if isinstance(response, str):
            response = ChatCompletion(
                id="",
                choices=[
                    Choice(
                        finish_reason="stop",
                        index=0,
                        message=ChatCompletionMessage(
                            role="assistant",
                            content=response
                        )
                    )
                ],
                created=0,
                model="",
                object="chat.completion"
            )
        # handle score
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
