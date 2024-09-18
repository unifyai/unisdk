import abc
import inspect
import rich.repr
from io import StringIO
from rich.console import Console
from pydantic import BaseModel, Extra
from typing import Optional, Union, Tuple, List, Dict, Mapping, Any
from openai.types.chat import (
    ChatCompletionToolParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionMessageParam,
    ChatCompletion as _ChatCompletion
)
from pydantic import create_model
from pydantic._internal._model_construction import ModelMetaclass
from openai._types import Headers, Query, Body
from openai.types.chat.completion_create_params import ResponseFormat
from openai.types.chat.chat_completion import ChatCompletionMessage, Choice

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

    def _prune_iterable(self, val):
        if not isinstance(val, dict) and not isinstance(val, list) and \
                not isinstance(val, tuple):
            return val
        elif isinstance(val, dict):
            return {k: self._prune_iterable(v) for k, v in val.items() if v is not None}
        elif isinstance(val, list):
            return [self._prune_iterable(v) for v in val if v is not None]
        else:
            return (self._prune_iterable(v) for v in val if v is not None)

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
        dct = self._prune_iterable(self.dict())
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
        return self._repr(self._prune())

    def __str__(self) -> str:
        return self._repr(self._prune())

    def __rich_repr__(self):
        pruned = self._prune()
        for k in pruned.model_fields:
            yield k, pruned.__dict__[k]


class Prompt(_FormattedBaseModel):
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
            user_message=None,
            system_message=None,
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


class ChatCompletion(_FormattedBaseModel, _ChatCompletion):

    def __init__(self, *args, **kwargs):
        if args:
            assert len(args) == 1 and isinstance(args[0], str), \
                "Can only accept one positional argument, and this must be a string " \
                "representing the user message."
            kwargs = {
                **dict(
                    id="",
                    choices=[
                        Choice(
                            finish_reason="stop",
                            index=0,
                            message=ChatCompletionMessage(
                                role="assistant",
                                content=args[0]
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

    def _chat_completion_pruned(self):
        return create_model(
            self.__class__.__name__,
            choices=(self.model_fields["choices"].annotation,
                     self.model_fields["choices"].default),
            __cls_kwargs__={"arbitrary_types_allowed": True}
        )(choices=self.dict()["choices"])

    def __repr__(self) -> str:
        return self._repr(self._chat_completion_pruned())

    def __str__(self) -> str:
        return self._repr(self._chat_completion_pruned())

    def __rich_repr__(self):
        pruned = self._chat_completion_pruned()
        for k in pruned.model_fields:
            yield k, pruned.__dict__[k]


class Datum(_FormattedBaseModel, extra=Extra.allow):
    prompt: Prompt

    def __init__(self, *args, **kwargs):
        if args:
            assert len(args) == 1, "Can only accept one positional argument."
            arg = args[0]
            if isinstance(arg, str):
                kwargs["prompt"] = Prompt(arg)
            elif isinstance(arg, Prompt):
                kwargs["prompt"] = arg
            else:
                raise Exception("Positional argument must either be a str or Prompt.")
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


class Score(_FormattedBaseModel, abc.ABC):
    score: Tuple[float, str]

    def __init__(self, value: float):
        assert value in self.config,\
            "value {} passed is not a valid value, " \
            "based on the config for this Score class {}".format(value, self.config)
        super().__init__(score=(value, self.config[value]))

    @property
    @abc.abstractmethod
    def config(self) -> Dict[float, str]:
        raise NotImplementedError
