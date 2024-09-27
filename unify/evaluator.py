import abc
import copy
import json
import inspect
from abc import abstractmethod
from typing import Type, Union, Optional, Tuple, Dict, List

from unify.agent import Agent
from unify.chat.clients import _Client, _UniLLMClient
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
        params = inspect.signature(self._evaluate).parameters
        # prune kwargs based on the arguments expected by _evaluate
        if "kwargs" not in params or params["kwargs"].annotation is not inspect._empty:
            kwargs = {k: v for k, v in kwargs.items() if k in params}
        # upcast or downcast prompt to the expected type
        expected_prompt_type = params["prompt"].annotation if "prompt" in params \
            else Prompt
        prompt = cast(prompt, expected_prompt_type)
        # upcast or downcast response to the expected type
        expected_response_type = params["response"].annotation if "response" in params \
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


class LLMJudge(Evaluator, abc.ABC):

    def __init__(
            self,
            client: _UniLLMClient,
            judge_prompt: Union[str, Prompt],
            name: Optional[str] = None,
            prompt_parser: Optional[Dict[str, List[Union[str, int]]]] = None,
            response_parser: Optional[Dict[str, List[Union[str, int]]]] = None,
            extra_parser: Optional[Dict[str, List[Union[str, int]]]] = None,
    ):
        """
        Creates an LLM as a Judge Evaluator.

        Args:
            client: The client to use as the LLM Judge.

            judge_prompt: The prompt for the judge to use when performing evaluations.

            name: The name to give to this LLM Judge evaluator, optional.

            prompt_parser: Function to parse the prompt and update corresponding
            placeholders in the judge user message and system message, optional.

            response_parser: Function to parse the response and update corresponding
            placeholders in the judge user message and system message, optional.

            extra_parser: Function to parse the extra fields provided alongside the
            prompt, and update corresponding placeholders in the judge user message and
            system message, optional.
        """
        self._client = client
        self._judge_prompt = cast(judge_prompt, Prompt)
        if prompt_parser is None:
            self._prompt_parser = {"user_message": ["messages", -1, "content"]}
        else:
            self._prompt_parser = prompt_parser
        if response_parser is None:
            self._response_parser = {
                "assistant_response": ["choices", 0, "message", "content"]
            }
        else:
            self._response_parser = response_parser
        self._extra_parser = extra_parser
        self._class_config_parser = {"class_config": None}
        super().__init__(name)

    @staticmethod
    def _parse(item, parse_rule):
        for idx in parse_rule:
            if isinstance(idx, int):
                if not isinstance(item, list) or len(item) < idx:
                    return
            elif not isinstance(item, dict) or idx not in item:
                return
            item = item[idx]
        return json.dumps(item) if isinstance(item, dict) else str(item)

    def _update_judge_messages(
            self,
            item: Union[Prompt, ChatCompletion, Dict],
            parser: Optional[Dict[str, List[Union[str, int]]]],
            messages: List
    ):
        if parser is None or item in (None, {}):
            return messages
        for key, parse_rule in parser.items():
            if parse_rule is None:
                content = json.dumps(item) if isinstance(item, dict) else str(item)
            else:
                content = self._parse(
                    item if isinstance(item, dict) else item.model_dump(), parse_rule
                )
            print("item: {}".format(item))
            print("parse_rule: {}".format(parse_rule))
            print("content: {}".format(content))
            messages = [
                {k: (v.replace("{" + key + "}", content) if k == "content" else v)
                 for k, v in msg.items()} for msg in messages
            ]
        return messages

    def _evaluate(
            self,
            prompt: Prompt,
            response: ChatCompletion,
            **kwargs
    ) -> Tuple[Union[bool, float, Score], Optional[str]]:
        messages = copy.deepcopy(self._judge_prompt.messages)
        for i, (item, parser) in enumerate(zip(
                (prompt, response, kwargs, self.class_config),
                (self._prompt_parser, self._response_parser, self._extra_parser,
                 self._class_config_parser)
        )):
            messages = self._update_judge_messages(
                copy.deepcopy(item),
                parser,
                messages
            )
        kw = self._judge_prompt.model_dump()
        kw["messages"] = messages
        judge_response = self._client.generate(**kw)
        judge_message = judge_response.choices[0].message.content
        judge_score = judge_message.split("\n")[-1]
        return float("".join(c for c in judge_score if c.isdigit() or c == "."))
        d = 0
