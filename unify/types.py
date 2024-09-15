import abc
import inspect
import rich.repr
from io import StringIO
from rich.console import Console
from pydantic import BaseModel, Extra
from typing import Optional, Union, Tuple, List, Dict, Mapping
from openai.types.chat import (
    ChatCompletionToolParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionMessageParam,
)
from pydantic import create_model
from pydantic._internal._model_construction import ModelMetaclass
from openai._types import Headers, Query, Body
from openai.types.chat.completion_create_params import ResponseFormat

import unify

RICH_CONSOLE = Console(file=StringIO())


class _Formatted(abc.ABC):

    @staticmethod
    def _repr(to_print):
        global RICH_CONSOLE
        RICH_CONSOLE.print(to_print)
        ret = RICH_CONSOLE.file.getvalue()
        RICH_CONSOLE.file.close()
        RICH_CONSOLE = Console(file=StringIO())
        # ToDO find more elegant way to flush this
        return ret

    def __repr__(self) -> str:
        return self._repr(self)

    def __str__(self) -> str:
        return self._repr(self)


@rich.repr.auto
class _FormattedBaseModel(_Formatted, BaseModel):

    def _prune_dict(self, val):
        if not isinstance(val, dict):
            return val
        return {k: self._prune_dict(v) for k, v in val.items() if v is not None}

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
        dct = self._prune_dict(self.dict())
        fields = self.model_fields
        if self.model_extra is not None:
            fields = {**fields, **self.model_extra}
        config = {k: (self._prune_pydantic(self._annotation(fields[k]), v),
                      self._default(fields[k])) for k, v in dct.items()}
        return create_model(self.__class__.__name__, **config)(**dct)

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

    def __init__(self, *args, **kwargs):
        if "messages" not in kwargs:
            kwargs["messages"] = list()
        if "system_message" in kwargs:
            kwargs["messages"] = \
                [{"content": kwargs["system_message"], "role": "system"}] + \
                kwargs["messages"]
            del kwargs["system_message"]
        if "user_message" in kwargs:
            assert not args, "If user_message is passed, positional args must be empty."
            kwargs["messages"] += [{"content": kwargs["user_message"], "role": "user"}]
            del kwargs["user_message"]
        elif args and isinstance(args[0], str):
            kwargs["messages"] += [{"content": args[0], "role": "user"}]
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


class Datum(_FormattedBaseModel, extra=Extra.allow):
    prompt: Prompt

    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], str):
            kwargs["prompt"] = Prompt(args[0])
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
        super().__init__(score=(value, self.config[value]))

    @property
    @abc.abstractmethod
    def config(self) -> Dict[float, str]:
        raise NotImplementedError
