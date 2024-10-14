from __future__ import annotations

import abc
import copy
import json
import re
from abc import abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union

from typing_extensions import Self
from unify.casting import cast
from unify.chat.clients import AsyncUnify, Unify
from unify.types import ChatCompletion, Prompt

from .utils.helpers import _validate_api_key


class Evaluator(abc.ABC):

    def __init__(
        self,
        score_config: Optional[Dict[float, str]],
        name: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Create an Evaluator.

        Args:
            name: The name for this evaluator.

            score_config: Either a derived Score subclass, or the configuration for the
            scores provided by this evaluator with the score floating values as keys and
            the  descriptions for these scores as the values.

            api_key: API key for accessing the Unify API. If None, it attempts to
            retrieve the API key from the environment variable UNIFY_KEY. Defaults to
            None.

        Raises:
            UnifyError: If the API key is missing.
        """
        self._name = name
        self._score_config = score_config
        self._api_key = _validate_api_key(api_key)

    # Properties #
    # -----------#

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def score_config(self) -> Dict[float, str]:
        return self._score_config

    # Setters #
    # --------#

    def set_name(self, value: str) -> Self:
        self._name = value
        return self

    def set_score_config(self, value: Dict[float, str]) -> Self:
        self._score_config = value
        return self

    # Abstract #
    # ---------#

    @abstractmethod
    def evaluate(self, *args, **kwargs) -> float:
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


class LLMJudge(Evaluator):

    def __init__(
        self,
        client: Union[Unify, AsyncUnify],
        prompt: Union[str, Prompt],
        score_config: Optional[Dict[float, str]],
        name: Optional[str] = None,
        input_parser: Optional[Dict[str, List[Union[str, int]]]] = None,
        response_parser: Optional[Dict[str, List[Union[str, int]]]] = None,
        include_rationale: bool = False,
        api_key: Optional[str] = None,
    ):
        """
        Creates an LLM as a Judge Evaluator.

        Args:
            client: The client to use as the LLM Judge.

            prompt: The prompt for the judge to use when performing evaluations.

            score_config: Either a derived Score subclass, or the configuration for the
            scores provided by this evaluator with the score floating values as keys and
            the  descriptions for these scores as the values.

            name: The name to give to this LLM Judge evaluator, optional.

            input_parser: Function to parse the input and update corresponding
            placeholders in the judge user message and system message, optional.

            response_parser: Function to parse the response and update corresponding
            placeholders in the judge user message and system message, optional.

            include_rationale: Whether to include the LLM's rationale as part of
            the evaluation response. Default is False.

            api_key: API key for accessing the Unify API. If None, it attempts to
            retrieve the API key from the environment variable UNIFY_KEY. Defaults to
            None.

        Raises:
            UnifyError: If the API key is missing.
        """
        self._client = client

        super().__init__(
            score_config=score_config,
            name=name if name is not None else self._client.endpoint,
            api_key=api_key,
        )

        self._prompt = cast(prompt, Prompt)
        assert (
            self._prompt.messages is not None
        ), "Judge prompt must have at least one message"
        self._prompt.messages[0]["content"] += self._create_judge_rubric()
        if input_parser is None:
            self._input_parser = {"user_message": None}
        else:
            self._input_parser = input_parser
        if response_parser is None:
            self._response_parser = {"assistant_response": None}
        else:
            self._response_parser = response_parser
        self._include_rationale = include_rationale

    # Properties

    @property
    def include_rationale(self) -> bool:
        return self._include_rationale

    @property
    def client(self) -> Union[Unify, AsyncUnify]:
        return self._client

    @property
    def prompt(self) -> Prompt:
        return self._prompt

    @property
    def input_parser(self) -> Dict[str, List[Union[str, int]]]:
        return self._input_parser

    @property
    def response_parser(self) -> Dict[str, List[Union[str, int]]]:
        return self._response_parser

    # Setters

    def set_include_rationale(self, value: bool) -> Self:
        self._include_rationale = value
        return self

    def set_client(self, value: Union[Unify, AsyncUnify]) -> Self:
        self._client = value
        return self

    def set_prompt(self, value: Union[str, Prompt]) -> Self:
        self._prompt = value
        return self

    def set_input_parser(self, value: Dict[str, List[Union[str, int]]]) -> Self:
        self._input_parser = value
        return self

    def set_response_parser(self, value: Dict[str, List[Union[str, int]]]) -> Self:
        self._response_parser = value
        return self

    @staticmethod
    def _extract_json_from_llm_response(response) -> str:
        return re.search(
            '\{[\n\r\s]*"assistant_rating":.*?}',
            response,
            flags=re.DOTALL | re.MULTILINE,
        ).group(0)

    def _parse_score_from_llm_response(self, response) -> Optional[float]:
        # noinspection PyBroadException
        try:
            judge_response = json.loads(self._extract_json_from_llm_response(response))
            rating = judge_response["assistant_rating"]
            if isinstance(rating, list):
                return float(rating[0])
            else:
                return float(rating)
        except Exception:
            return

    def _create_judge_rubric(self):
        prompt = (
            "First provide your explanation, "
            "then write down your final rating according to the "
            "following guidelines:"
        )
        for score_val, description in self.score_config.items():
            head_str = f"""\n\t - "{score_val}" """
            head_str += f""": {description}"""
            prompt += head_str

        prompt += """\nAfter that, you must output your final verdict in JSON by
        **strictly** following this format:

        {"assistant_rating": RATING}

        Do not output anything else after your final verdict, but make sure you do give
        a verdict, that's the most important part!"""
        return prompt

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
        messages: List,
    ):
        if parser is None or item in (None, {}):
            return messages
        for key, parse_rule in parser.items():
            if parse_rule is None:
                content = json.dumps(item) if isinstance(item, dict) else str(item)
            else:
                content = self._parse(
                    item if isinstance(item, dict) else item.model_dump(),
                    parse_rule,
                )
            messages = [
                {
                    k: (v.replace("{" + key + "}", content) if k == "content" else v)
                    for k, v in msg.items()
                }
                for msg in messages
            ]
        return messages

    def evaluate(
        self,
        input: Any,
        response: Any,
    ) -> Union[float, Tuple[float, Union[str, ChatCompletion]]]:
        messages = copy.deepcopy(self._prompt.messages)
        for i, (item, parser) in enumerate(
            zip((input, response), (self._input_parser, self._response_parser)),
        ):
            messages = self._update_judge_messages(
                copy.deepcopy(item),
                parser,
                messages,
            )
        kw = self._prompt.model_dump()
        kw["messages"] = messages
        judge_response = self._client.generate(**kw)
        if self._client.return_full_completion:
            judge_response = judge_response.choices[0].message.content
        else:
            judge_response = judge_response
        score = self._parse_score_from_llm_response(judge_response)
        if self._include_rationale:
            return score, judge_response
        return score


class DefaultLLMJudge(LLMJudge):

    def __init__(
        self,
        client: Union[Unify, AsyncUnify],
        prompt: Optional[Union[str, Prompt]] = None,
        score_config: Optional[Dict[float, str]] = None,
        name: Optional[str] = None,
        input_parser: Optional[Dict[str, Union[List[Union[str, int]], None]]] = None,
        response_parser: Optional[Dict[str, Union[List[Union[str, int]], None]]] = None,
        include_rationale: bool = False,
        api_key: Optional[str] = None,
    ):
        """
        Creates an LLM as a Judge Evaluator.

        Args:
            client: The client to use as the LLM Judge.

            prompt: The prompt for the judge to use when performing evaluations.

            score_config: Either a derived Score subclass, or the configuration for the
            scores provided by this evaluator with the score floating values as keys and
            the  descriptions for these scores as the values.

            name: The name to give to this LLM Judge evaluator, optional.

            input_parser: Function to parse the input and update corresponding
            placeholders in the judge user message and system message, optional.

            response_parser: Function to parse the response and update corresponding
            placeholders in the judge user message and system message, optional.

            include_rationale: Whether to include the LLM's rationale as part of
            the evaluation response. Default is False.

            api_key: API key for accessing the Unify API. If None, it attempts to
            retrieve the API key from the environment variable UNIFY_KEY. Defaults to
            None.

        Raises:
            UnifyError: If the API key is missing.
        """
        if score_config is None:
            score_config = {0.0: "bad", 0.5: "good", 0.8: "very good", 1.0: "excellent"}
        sys = "[System]\n"
        "Please act as an impartial judge and evaluate the quality of the response "
        "provided by an assistant to the user message displayed below. "
        "Your job is to evaluate how good the assistant's response is. "
        "Your evaluation should consider correctness and helpfulness. "
        "Identify any mistakes. "
        "Be as objective as possible."
        template_no_ref = """
        {score_config}

        [start of user message]
        {user_message}
        [end of user message]

        [start of assistant response]
        {assistant_response}
        [end of assistant response]"""
        if prompt is None:
            prompt = Prompt(
                messages=[
                    {
                        "role": "system",
                        "content": sys,
                    },
                    {
                        "role": "user",
                        "content": template_no_ref,
                    },
                ],
            )
        elif isinstance(prompt, str):
            prompt = cast(prompt, Prompt)

        if name is None:
            name = "default_llm_judge<{}>".format(client.endpoint)
        super().__init__(
            score_config=score_config,
            prompt=prompt,
            name=name,
            client=client,
            input_parser=input_parser,
            response_parser=response_parser,
            include_rationale=include_rationale,
            api_key=api_key,
        )


class LLMJury(Evaluator):

    def __init__(
        self,
        judges: List[LLMJudge],
        name: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Creates an LLM Jury Evaluator.

        Args:
            judges: The list of judges to use in the Jury.

            name: The name to give to this LLM Jury evaluator, optional.

            api_key: API key for accessing the Unify API. If None, it attempts to
            retrieve the API key from the environment variable UNIFY_KEY. Defaults to
            None.
        """
        self._judges = judges
        assert all(
            j.score_config == judges[0].score_config for j in judges
        ), "All judges in a Jury must have the same score configuration."
        super().__init__(judges[0].score_config, name, api_key)

    # noinspection PyMethodOverriding
    def evaluate(
        self,
        input: Any,
        response: Any,
    ) -> Dict[str, Union[float, Tuple[float, Union[str, ChatCompletion]]]]:
        evaluations = dict()
        for judge in self._judges:
            evaluations[judge.name] = judge.evaluate(input, response)
        return evaluations

    @property
    def judges(self) -> List[LLMJudge]:
        return self._judges
