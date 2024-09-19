import abc
import copy
import inspect
import rich.repr
from io import StringIO
from rich.console import Console
from pydantic import BaseModel, Extra, ConfigDict
from pydantic import create_model
from pydantic._internal._model_construction import ModelMetaclass
from typing import Optional, Union, Tuple, List, Dict, Mapping, Type
from openai._types import Query, Body
from openai.types.chat import (
    ChatCompletionToolParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionMessageParam,
    ChatCompletion as _ChatCompletion
)
from openai.types.completion_usage import CompletionUsage as _CompletionUsage
from openai.types.chat.completion_create_params import ResponseFormat
from openai.types.chat.chat_completion import \
    ChatCompletionMessage as _ChatCompletionMessage, Choice as _Choice

import unify

RICH_CONSOLE = Console(file=StringIO())


class _Formatted(abc.ABC):

    @staticmethod
    def _repr(to_print):
        # ToDO find more elegant way to do this
        global RICH_CONSOLE
        with RICH_CONSOLE.capture() as capture:
            RICH_CONSOLE.print(to_print)
        return capture.get()

    def __repr__(self) -> str:
        return self._repr(self)

    def __str__(self) -> str:
        return self._repr(self)


@rich.repr.auto
class _FormattedBaseModel(_Formatted, BaseModel):

    def _prune_dict(self, val, prune_policy):

        def keep(v, k=None, prune_pol=None):
            if v is None:
                return False
            if not prune_pol:
                return True
            if isinstance(prune_pol, dict) and \
                    "keep" not in prune_pol and "skip" not in prune_pol:
                return True
            if "keep" in prune_pol:
                if k not in prune_pol["keep"]:
                    return False
                prune_val = prune_pol["keep"][k]
                return prune_val is None or prune_val == v
            elif "skip" in prune_pol:
                if k not in prune_pol["skip"]:
                    return True
                prune_val = prune_pol["skip"][k]
                return prune_val is not None and prune_val != v
            else:
                raise Exception("expected prune_pol to contain either 'keep' or 'skip',"
                                "but neither were present: {}.".format(prune_pol))

        if not isinstance(val, dict) and not isinstance(val, list) and \
                not isinstance(val, tuple):
            return val
        elif isinstance(val, dict):
            return {
                k: self._prune_dict(
                    v, prune_policy[k] if
                    (isinstance(prune_policy, dict) and k in prune_policy) else None
                ) for k, v in val.items() if keep(v, k, prune_policy)
            }
        elif isinstance(val, list):
            return [
                self._prune_dict(
                    v, prune_policy[i] if
                    (isinstance(prune_policy, list ) and i < len(prune_policy))
                    else None
                ) for i, v in enumerate(val) if keep(v, prune_pol=prune_policy)
            ]
        else:
            return (
                self._prune_dict(
                    v, prune_policy[i] if
                    (isinstance(prune_policy, tuple) and i < len(prune_policy))
                    else None
                ) for i, v in enumerate(val) if keep(v, prune_pol=prune_policy)
            )

    def _prune_pydantic(self, val, dct):
        if not inspect.isclass(val) or not issubclass(val, BaseModel):
            return val
        config = {k: (self._prune_pydantic(val.model_fields[k].annotation, v),
                      val.model_fields[k].default) for k, v in dct.items()}
        if isinstance(val, ModelMetaclass):
            name = val.__qualname__
        else:
            name = val.__class__.__name__
        return create_model(name, **config)

    @staticmethod
    def _annotation(v):
        if hasattr(v, "annotation"):
            return v.annotation
        return type(v)

    @staticmethod
    def _default(v):
        if hasattr(v, "default"):
            return v.default
        return None

    def _prune(self):
        prune_policy = unify.key_repr(self)
        dct = self._prune_dict(self.dict(), prune_policy)
        fields = self.model_fields
        if self.model_extra is not None:
            fields = {**fields, **self.model_extra}
        config = {k: (self._prune_pydantic(self._annotation(fields[k]), v),
                      self._default(fields[k])) for k, v in dct.items()}
        return create_model(
            self.__class__.__name__,
            **config,
            __cls_kwargs__={"arbitrary_types_allowed": True}
        )(**dct)

    def __repr__(self) -> str:
        return self._repr(self._prune() if unify.repr_mode() == "concise" else self)

    def __str__(self) -> str:
        return self._repr(self._prune() if unify.repr_mode() == "concise" else self)

    def __rich_repr__(self):
        rep = self._prune() if unify.repr_mode() == "concise" else self
        for k in rep.model_fields:
            yield k, rep.__dict__[k]

    def full_repr(self):
        """
        Return the full un-pruned representation, regardless of the mode currently set.
        """
        with unify.ReprMode("verbose"):
            return self._repr(self)


class Prompt(_FormattedBaseModel):
    model_config = ConfigDict(extra="forbid")
    messages: Optional[List[ChatCompletionMessageParam]] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, int]] = None
    logprobs: Optional[bool] = None
    top_logprobs: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    n: Optional[int] = None
    presence_penalty: Optional[float] = None
    response_format: Optional[ResponseFormat] = None
    seed: Optional[int] = None
    stop: Union[Optional[str], List[str]] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    tools: Optional[List[ChatCompletionToolParam]] = None
    tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None
    parallel_tool_calls: Optional[bool] = None
    # extra_headers: Optional[Headers] = None  # ToDo: fix Omit error
    extra_headers: Optional[Mapping[str, str]] = None
    extra_query: Optional[Query] = None
    extra_body: Optional[Body] = None

    def __init__(
            self,
            user_message: Optional[str] = None,
            system_message: Optional[str] = None,
            **kwargs
    ):
        """
        Create Prompt instance.

        Args:
            user_message: The user message, optional.

            system_message: The system message, optional.

            kwargs: All fields expressed in the pydantic type.

        Returns:
            The pydantic Prompt instance.
        """
        if "messages" not in kwargs:
            kwargs["messages"] = list()
        if system_message:
            kwargs["messages"] = \
                [{"content": system_message, "role": "system"}] + \
                kwargs["messages"]
        if user_message:
            kwargs["messages"] += [{"content": user_message, "role": "user"}]
        if not kwargs["messages"]:
            kwargs["messages"] = None
        super().__init__(**kwargs)

    def __add__(self, other):
        return unify.Dataset(self) +\
               (other if isinstance(other, unify.Dataset) else unify.Dataset(other))

    def __sub__(self, other):
        return unify.Dataset(self) -\
               (other if isinstance(other, unify.Dataset) else unify.Dataset(other))

    def __radd__(self, other):
        return (other if isinstance(other, unify.Dataset) else unify.Dataset(other)) +\
               unify.Dataset(self)

    def __rsub__(self, other):
        return (other if isinstance(other, unify.Dataset) else unify.Dataset(other)) -\
               unify.Dataset(self)

    def __hash__(self):
        return hash(str(self))


class ChatCompletionMessage(_FormattedBaseModel, _ChatCompletionMessage):
    model_config = ConfigDict(extra="forbid")


class Choice(_FormattedBaseModel, _Choice):
    model_config = ConfigDict(extra="forbid")
    # only override pydantic types  which require FormattedBaseModel
    message: ChatCompletionMessage


class CompletionUsage(_FormattedBaseModel, _CompletionUsage):
    model_config = ConfigDict(extra="forbid")
    # cost is an extra field we've added, not in the OpenAI standard
    cost: float


class ChatCompletion(_FormattedBaseModel, _ChatCompletion):
    model_config = ConfigDict(extra="forbid")
    # only override pydantic types  which require FormattedBaseModel
    choices: List[Choice]
    usage: Optional[CompletionUsage] = None

    def __init__(self, assistant_message: Optional[str] = None, **kwargs):
        """
        Create ChatCompletion instance.

        Args:
            assistant_message: The assistant message, optional.

        Returns:
            The pydantic ChatCompletion instance.
        """
        if assistant_message:
            kwargs = {
                **dict(
                    id="",
                    choices=[
                        Choice(
                            finish_reason="stop",
                            index=0,
                            message=ChatCompletionMessage(
                                role="assistant",
                                content=assistant_message
                            )
                        )
                    ],
                    created=0,
                    model="",
                    object="chat.completion",
                    **kwargs
                ),
                **kwargs
            }
        super().__init__(**kwargs)


class Datum(_FormattedBaseModel, extra=Extra.allow):
    prompt: Prompt

    def __init__(self, prompt: Optional[Union[str, Prompt]]):
        """
        Create Datum instance.

        Args:
            prompt: The prompt, either as a user message or as the full prompt.

        Returns:
            The pydantic Datum instance.
        """
        if isinstance(prompt, str):
            prompt = Prompt(prompt)
        super().__init__(prompt=prompt)

    def __add__(self, other):
        return unify.Dataset(self) +\
               (other if isinstance(other, unify.Dataset) else unify.Dataset(other))

    def __sub__(self, other):
        return unify.Dataset(self) -\
               (other if isinstance(other, unify.Dataset) else unify.Dataset(other))

    def __radd__(self, other):
        return (other if isinstance(other, unify.Dataset) else unify.Dataset(other)) +\
               unify.Dataset(self)

    def __rsub__(self, other):
        return (other if isinstance(other, unify.Dataset) else unify.Dataset(other)) -\
               unify.Dataset(self)

    def __hash__(self):
        return hash(str(self))


class Score(_FormattedBaseModel, abc.ABC):
    model_config = ConfigDict(extra="forbid")
    score: Tuple[float, str]

    def __init__(self, value: float):
        """
        Create Score instance.

        Args:
            value: The value of the assigned score

        Returns:
            The pydantic Score instance, with associated value and class description
        """
        assert value in self.config,\
            "value {} passed is not a valid value, " \
            "based on the config for this Score class {}".format(value, self.config)
        super().__init__(score=(value, self.config[value]))

    @property
    @abc.abstractmethod
    def config(self) -> Dict[float, str]:
        raise NotImplementedError
