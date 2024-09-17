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
            prompt: Union[str, Prompt],
            response: Union[str, ChatCompletion],
            **kwargs
    ) -> Union[bool, float, Score]:
        """
        Evaluate the given response for this input prompt, with optional extra data.

        Args:
            prompt: The user message or the full input prompt being responded to.

            response: The response which is being evaluated, either as just the most
            recent assistant message, or the full chat completion.

            kwargs: Extra information relevant to the prompt, as is stored in the Datum.

        Returns:
            The score, either as a boolean, a float, or the full Score instance.
        """
        raise NotImplemented

    def evaluate(
            self,
            prompt: Union[str, Prompt],
            response: Union[ChatCompletion, str],
            agent: Union[str, _Client, Agent],
            **kwargs
    ):
        """
        Evaluate the given response for this input prompt, with optional extra data.

        Args:
            prompt: The user message or the full input prompt being responded to.

            response: The response which is being evaluated, either as just the most
            recent assistant message, or the full chat completion.

            agent: The agent that made the response, which is being evaluated.

            kwargs: Extra information relevant to the prompt, as is stored in the Datum.

        Returns:
            An Evaluation instance, containing the prompt, response, agent, score and
            optional extra data used during the evaluation.
        """
        score = self._evaluate(prompt, response, **kwargs)
        # handle datum
        if isinstance(prompt, str):
            prompt = Prompt(prompt)
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
            prompt=prompt,
            response=response,
            agent=agent,
            score=score,
            **kwargs
        )
