from __future__ import annotations
import re
import abc
import copy
import json
import inspect
from pydantic import BaseModel
from abc import abstractmethod
from typing_extensions import Self
from typing import Type, Union, Optional, Tuple, Dict, List

import unify
from unify.agent import Agent
from unify.evaluation import Evaluation, EvaluationSet, Scores, Rationales
from unify.chat.clients import _Client, Unify, AsyncUnify
from unify.casting import cast
from .utils.helpers import _validate_api_key
from .utils.evaluators import create_evaluator, list_evaluators, delete_evaluator
from unify.types import Score, Prompt, ChatCompletion


class Evaluator(abc.ABC):

    def __init__(
            self,
            score_config: Optional[Union[Score, Type[Score], Dict[float, str]]] = None,
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
        if isinstance(score_config, dict):
            self._score_config = score_config
            self._score_class = unify.Score(config=score_config)
        elif isinstance(score_config, type) and issubclass(score_config, Score):
            score_config = score_config()
            self._score_config = score_config.config
            self._score_class = score_config
        elif isinstance(score_config, Score):
            self._score_config = score_config.config
            self._score_class = score_config
        else:
            raise Exception("score_config must either be a Score subclass or a dict.")
        self._api_key = _validate_api_key(api_key)

    # Properties #
    # -----------#

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def score_config(self) -> Dict[float, str]:
        return self._score_config

    @property
    def score_class(self) -> Score:
        return self._score_class

    # Setters #
    # --------#

    def set_name(self, value: str):
        self._name = value

    # Abstract #
    # ---------#

    @abstractmethod
    def _evaluate(
            self,
            prompt: Union[str, Prompt],
            response: Union[str, ChatCompletion],
            **kwargs
    ) -> Union[
            Union[bool, float, Score],
            Tuple[Union[bool, float, Score], Union[str, Dict, EvaluationSet]]
    ]:
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

    # Private #
    # --------#

    def _assert_name_exists(self) -> None:
        assert self._name is not None, (
            "Evaluator name must be specified in order to upload or download "
            "to or from a corresponding Evaluator in your upstream account. "
            "You can simply use .set_name() and set it to the same name as your "
            "upstream evaluator, or create a new name if it doesn't yet exist upstream."
        )

    # Public #
    # -------#

    def upload(self, description: Optional[str] = None, overwrite: bool = False) \
            -> Self:
        """
        Register the Evaluator to your account upstream.

        Args:

            description:
            Optional description of the evaluator, to be registered upstream.

            overwrite:
            Whether to overwrite the entry for an existing evaluator with the
            same name if it already exists.

        Returns:
            This Evaluator after the upload, useful for chaining methods.
        """
        self._assert_name_exists()
        if description is None and self.__doc__ is not None:
            description = self.__doc__
        evaluator_config = dict(
            name=self._name,
            class_config=[{"label": label, "score": score, "description": ""}
                          for score, label in self._score_config.items()],
            # description=description,  # ToDo: uncomment once orchestra DB is updated
            client_side=True
        )
        if overwrite and self._name in list_evaluators():
            delete_evaluator(self._name)
        create_evaluator(evaluator_config=evaluator_config, api_key=self._api_key)
        return self

    def evaluate(
            self,
            prompt: Union[str, Prompt],
            response: Union[ChatCompletion, str],
            agent: Union[str, _Client, Agent],
            **kwargs
    ) -> Union[Evaluation, EvaluationSet]:
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
        if "kwargs" not in params:
            kwargs = {k: v for k, v in kwargs.items() if k in params}
        if "agent" in params:
            kwargs["agent"] = agent
        # upcast or downcast prompt to the expected type
        if "prompt" in params:
            annotation = params["prompt"].annotation
            if isinstance(annotation, str):
                expected_prompt_type = eval(annotation)
            else:
                expected_prompt_type = annotation
        else:
            expected_prompt_type = Prompt
        prompt = cast(prompt, expected_prompt_type)
        # upcast or downcast response to the expected type
        if "response" in params:
            annotation = params["response"].annotation
            if isinstance(annotation, str):
                expected_response_type = eval(annotation)
            else:
                expected_response_type = annotation
        else:
            expected_response_type = ChatCompletion
        response = cast(response, expected_response_type)

        # perform the evaluation
        ret = self._evaluate(prompt, response, **kwargs)
        score, rationale = ret if isinstance(ret, tuple) else (ret, None)

        # upcast to full type for storage in Evaluation

        # prompt upcasting
        prompt = cast(prompt, Prompt)
        # response upcasting
        if isinstance(response, dict):
            response = {k: cast(v, ChatCompletion) for k, v in response.items()}
        else:
            response = cast(response, ChatCompletion)
        # remove agent from kwargs if present
        if "agent" in kwargs:
            del kwargs["agent"]
        # score upcasting
        if isinstance(score, dict):
            score = Scores({k: self._score_class(v) for k, v in score.items()})
        elif score is not None:
            score = self._score_class(score)
        if isinstance(rationale, dict):
            rationale = Rationales(rationale)
        # return evaluation
        return Evaluation(
            prompt=prompt,
            response=response,
            agent=agent,
            score=score,
            evaluator=self,
            rationale=rationale,
            **kwargs
            )


class LLMJudge(Evaluator):

    def __init__(
            self,
            score_config: Optional[Union[Score, Type[Score], Dict[float, str]]] = None,
            name: Optional[str] = None,
            client: Union[Unify, AsyncUnify] = None,
            prompt: Union[str, Prompt] = None,
            prompt_parser: Optional[Dict[str, List[Union[str, int]]]] = None,
            response_parser: Optional[Dict[str, List[Union[str, int]]]] = None,
            extra_parser: Optional[Dict[str, List[Union[str, int]]]] = None,
            include_rationale: bool = False,
            api_key: Optional[str] = None,
    ):
        """
        Creates an LLM as a Judge Evaluator.

        Args:
            score_config: Either a derived Score subclass, or the configuration for the
            scores provided by this evaluator with the score floating values as keys and
            the  descriptions for these scores as the values.

            name: The name to give to this LLM Judge evaluator, optional.

            client: The client to use as the LLM Judge.

            prompt: The prompt for the judge to use when performing evaluations.

            prompt_parser: Function to parse the prompt and update corresponding
            placeholders in the judge user message and system message, optional.

            response_parser: Function to parse the response and update corresponding
            placeholders in the judge user message and system message, optional.

            extra_parser: Function to parse the extra fields provided alongside the
            prompt, and update corresponding placeholders in the judge user message and
            system message, optional.

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
            api_key=api_key
        )

        self._prompt = cast(prompt, Prompt)
        assert self._prompt.messages is not None, \
            "Judge prompt must have at least one message"
        self._prompt.messages[0]["content"] += self._create_judge_rubric()
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
        self._include_rationale = include_rationale
        self._score_config_parser = {"score_config": None}

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
    def prompt_parser(self) -> Dict[str, List[Union[str, int]]]:
        return self._prompt_parser

    @property
    def response_parser(self) -> Dict[str, List[Union[str, int]]]:
        return self._response_parser

    @property
    def extra_parser(self) -> Dict[str, List[Union[str, int]]]:
        return self._extra_parser

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

    def set_prompt_parser(self, value: Dict[str, List[Union[str, int]]]) -> Self:
        self._prompt_parser = value
        return self

    def set_response_parser(self, value: Dict[str, List[Union[str, int]]]) -> Self:
        self._response_parser = value
        return self

    def set_extra_parser(self, value: Dict[str, List[Union[str, int]]]) -> Self:
        self._extra_parser = value
        return self

    @staticmethod
    def _extract_json_from_llm_response(response) -> str:
        return re.search(
            '\{[\n\r\s]*"assistant_rating":.*?}',
            response, flags=re.DOTALL | re.MULTILINE
        ).group(0)

    def _parse_score_from_llm_response(self, response) -> Optional[float]:
        # noinspection PyBroadException
        try:
            judge_response = json.loads(self._extract_json_from_llm_response(response))
            rating = judge_response["assistant_rating"]
            if isinstance(rating, list):
                return rating[0]
            else:
                return float(rating)
        except Exception:
            return

    def _create_judge_rubric(self):
        prompt = ("First provide your explanation, "
                  "then write down your final rating according to the "
                  "following guidelines:")
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
    ) -> Union[Tuple[float, str], float]:
        messages = copy.deepcopy(self._prompt.messages)
        for i, (item, parser) in enumerate(zip(
                (prompt, response, kwargs, self.score_config),
                (self._prompt_parser, self._response_parser, self._extra_parser,
                 self._score_config_parser)
        )):
            messages = self._update_judge_messages(
                copy.deepcopy(item),
                parser,
                messages
            )
        kw = self._prompt.model_dump()
        kw["messages"] = messages
        judge_response = self._client.generate(**kw)
        if self._client.return_full_completion:
            judge_message = judge_response.choices[0].message.content
        else:
            judge_message = judge_response
        score = self._parse_score_from_llm_response(judge_message)
        if self._include_rationale:
            return score, judge_message
        return score

    # Public #
    # -------#

    @staticmethod
    def from_upstream(name: str) -> LLMJudge:
        """
        Return an LLMJudge instance, initialized from the upstream LLMJudge
        configuration.

        Args:
            name:
            The name of the upstream LLM Judge to create a local instance for.

        Returns:
            The LLMJudge instance.
        """
        judge_config = unify.get_evaluator(name)
        assert len(judge_config["judge_models"]) == 1, \
            "Only one judge is permitted when initializing an LLMJudge instance."
        return LLMJudge(
            score_config=judge_config["score_config"],
            name=name,
            client=unify.Unify(judge_config["judge_models"][0]),
            prompt=judge_config["judge_prompt"],
            prompt_parser=judge_config["prompt_parser"],
            response_parser=judge_config["response_parser"],
            # extra_parser=judge_config["extra_parser"],
        )

    def upload(self, description: Optional[str] = None, overwrite: bool = False) \
            -> Self:
        """
        Register the Evaluator to your account upstream.

        Args:

            description:
            Optional description of the evaluator, to be registered upstream.

            overwrite:
            Whether to overwrite the entry for an existing evaluator with the
            same name if it already exists.

        Returns:
            This Evaluator after the upload, useful for chaining methods.
        """
        self._assert_name_exists()
        if description is None and self.__doc__ is not None:
            description = self.__doc__
        evaluator_config = dict(
            name=self._name,
            judge_prompt=self._prompt.model_dump(),
            prompt_parser=self._prompt_parser,
            response_parser=self._response_parser,
            # extra_parser=self._extra_parser,  # ToDo: uncomment once orchestra updated
            class_config=[{"label": label, "score": score}
                          for score, label in self.score_config.items()],
            # score_config=[{"label": label, "score": score}
            #               for score, label in self.score_config.items()],
            # ToDo: uncomment once orchestra updated
            # description=description,  # ToDo: uncomment once orchestra DB updated
            judge_models=self.client.endpoint,
            client_side=False
        )
        if overwrite and self._name in list_evaluators():
            delete_evaluator(self._name)
        create_evaluator(evaluator_config=evaluator_config, api_key=self._api_key)
        return self


class DefaultJudgeScore(Score):

    @property
    def config(self) -> Dict[float, str]:
        return {
            0.0: "bad",
            0.5: "good",
            0.8: "very good",
            1.0: "excellent"
        }


class DefaultLLMJudge(LLMJudge):

    def __init__(
            self,
            client: Union[Unify, AsyncUnify]
    ):
        """
        Create a default Judge, which uses a standard task-agnostic score and a generic
        system prompt. This should judge work okay on a range of tasks, but the best
        performance will be achieved by subclassing LLMJudge and creating your own.

        Args:
            client: The client which holds the LLM used under the hood for judging.
        """
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
        super().__init__(
            DefaultJudgeScore,
            client=client,
            prompt=prompt,
            name="default_llm_judge<{}>".format(client.endpoint)
        )


class LLMJury(Evaluator, abc.ABC):

    def __init__(
            self,
            score_config: Optional[Union[Score, Type[Score], Dict[float, str]]] = None,
            judges: List[LLMJudge] = None,
            name: Optional[str] = None,
            include_rationale: bool = False,
    ):
        """
        Creates an LLM as a Judge Evaluator.

        Args:
            score_config: Either a derived Score subclass, or the configuration for the
            scores provided by this evaluator with the score floating values as keys and
            the  descriptions for these scores as the values.

            judges: The client to use as the LLM Judge.

            name: The name to give to this LLM Judge evaluator, optional.

            include_rationale: Whether to include the LLM's rationale as part of
            the evaluation response. Default is False.
        """
        judges = [copy.copy(judge) for judge in judges]
        for judge in judges:
            judge.set_include_rationale(include_rationale)

        self._judges = judges
        self._include_rationale = include_rationale
        self._num_judges = len(judges)
        super().__init__(score_config, name)

    # noinspection PyMethodOverriding
    def _evaluate(
            self,
            prompt: Prompt,
            response: ChatCompletion,
            agent: Union[str, _Client, Agent],
            **kwargs
    ) -> Tuple[Dict[str, Score], Dict[str, Union[str, Dict, BaseModel]]]:
        scores = dict()
        rationales = dict()
        for judge in self._judges:
            evaluation = judge.evaluate(prompt, response, agent, **kwargs)
            scores[judge.name] = evaluation.score
            rationales[judge.name] = evaluation.rationale
        return scores, rationales

    def _assert_identical_judge_configs(self):
        # ToDo: remove these checks once we support evaluators in orchestra as a
        #  collection of independent (separately uploaded) judges.
        error_msg = ("All Judges must have identical configurations in order to upload "
                     "to your user account for deployment on the server side. If you "
                     "would like to register this as a client side evaluator, "
                     "then set client_side=True when calling upload")
        assert all(j.prompt == self._judges[0].prompt for j in self._judges), error_msg
        assert all(j.prompt_parser == self._judges[0].prompt_parser
                   for j in self._judges), error_msg
        assert all(j.response_parser == self._judges[0].response_parser
                   for j in self._judges), error_msg
        # assert all(j.extra_parser == self._judges[0].extra_parser
        #            for j in self._judges), error_msg

    @staticmethod
    def from_upstream(name: str) -> LLMJury:
        """
        Return an LLMJury instance, initialized from the upstream LLMJury configuration.

        Args:
            name:
            The name of the upstream LLM Jury to create a local instance for.

        Returns:
            The LLMJury instance.
        """
        judge_config = unify.get_evaluator(name)
        assert len(judge_config["judge_models"]) > 1, \
            "More than one judge is required to initialize an LLMJury instance."
        judges = [
            LLMJudge(
                score_config=judge_config["score_config"],
                name=endpoint,
                client=unify.Unify(endpoint),
                prompt=judge_config["judge_prompt"],
                prompt_parser=judge_config["prompt_parser"],
                response_parser=judge_config["response_parser"],
                # extra_parser=judge_config["extra_parser"],
            ) for endpoint in judge_config["judge_models"]
        ]
        return LLMJury(
            score_config=judge_config["score_config"],
            judges=judges,
            name=name
        )

    def upload(
            self,
            description: Optional[str] = None,
            overwrite: bool = False,
            client_side: bool = False
    ) -> Self:
        """
        Register the Evaluator to your account upstream.

        Args:

            description:
            Optional description of the evaluator, to be registered upstream.

            overwrite:
            Whether to overwrite the entry for an existing evaluator with the
            same name if it already exists.

            client_side:
            Whether to register this as a client-side evaluator. If the judges each have
            unique configurations, then this is required.

        Returns:
            This Evaluator after the upload, useful for chaining methods.
        """
        self._assert_name_exists()
        self._assert_identical_judge_configs()
        if description is None and self.__doc__ is not None:
            description = self.__doc__
        evaluator_config = dict(
            name=self._name,
            judge_prompt=self._judges[0].prompt.model_dump(),
            prompt_parser=self._judges[0].prompt_parser,
            response_parser=self._judges[0].response_parser,
            # extra_parser=self._judges[0].extra_parser,
            # ToDo: uncomment once orchestra updated
            class_config=[{"label": label, "score": score}
                          for score, label in self.score_config.items()],
            # score_config=[{"label": label, "score": score}
            #               for score, label in self.score_config.items()],
            # ToDo: uncomment once orchestra updated
            # description=description,  # ToDo: uncomment once orchestra DB updated
            judge_models=[j.client.endpoint for j in self._judges],
            client_side=client_side
        )
        if overwrite and self._name in list_evaluators():
            delete_evaluator(self._name)
        create_evaluator(evaluator_config=evaluator_config, api_key=self._api_key)
        return self

    @property
    def judges(self) -> List[LLMJudge]:
        return self._judges
