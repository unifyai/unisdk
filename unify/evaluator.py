import abc
from abc import abstractmethod
from typing import Type, Union, Optional, Tuple, Dict

from unify.agent import Agent
from unify.chat.clients import _Client
from unify.evaluation import Evaluation
from unify.casting import cast
from unify.types import Score, Prompt, ChatCompletion


class Evaluator(abc.ABC):

    def __init__(
            self,
            name: Optional[str] = None
    ):
        """
        Create an Evaluator.

        Args:
            name: The name for this evaluator.
        """
        self._name = name

    # Properties #
    # -----------#

    @property
    def name(self) -> Optional[str]:
        return self._name

    # Setters #
    # --------#

    def set_name(self, name: str):
        self._name = name

    # Abstract #
    # ---------#

    @property
    def class_config(self) -> Dict[float, str]:
        return self.scorer().config

    @property
    @abstractmethod
    def scorer(self) -> Type[Score]:
        raise NotImplemented

    @abstractmethod
    def _evaluate(
            self,
            prompt: Union[str, Prompt],
            response: Union[str, ChatCompletion],
            **kwargs
    ) -> Tuple[Union[bool, float, Score], Optional[str]]:
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

        # upcast or downcast inputs

        # get type hints for self._evaluation, if they exist
        eval_ann = self._evaluate.__annotations__
        # prune kwargs based on the arguments expected by _evaluate
        kwargs = {k: v for k, v in kwargs.items() if k in eval_ann}
        # upcast or downcast prompt to the expected type
        expected_prompt_type = eval_ann["prompt"] if "prompt" in eval_ann else Prompt
        prompt = cast(prompt, expected_prompt_type)
        # upcast or downcast response to the expected type
        expected_response_type = eval_ann["response"] if "response" in eval_ann \
            else ChatCompletion
        response = cast(response, expected_response_type)

        # perform the evaluation
        ret = self._evaluate(prompt, response, **kwargs)
        score, rationale = ret if isinstance(ret, tuple) else (ret, None)

        # upcast to full type for storage in Evaluation

        # prompt upcasting
        prompt = cast(prompt, Prompt)
        # response upcasting
        response = cast(response, ChatCompletion)
        # score upcasting
        score = cast(score, self.scorer)
        # return evaluation
        return Evaluation(
            prompt=prompt,
            response=response,
            agent=agent,
            score=score,
            rationale=rationale,
            **kwargs
        )
