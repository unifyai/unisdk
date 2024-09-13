import abc
import inspect
import rich.repr
from io import StringIO
from rich.console import Console
from pydantic import BaseModel, Extra
from typing import Optional, Union, List, Dict, Mapping
from openai.types.chat import (
    ChatCompletionToolParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionMessageParam,
)
from pydantic import create_model
from pydantic._internal._model_construction import ModelMetaclass
from openai._types import Headers, Query, Body
from openai.types.chat.completion_create_params import ResponseFormat

RICH_CONSOLE = Console(file=StringIO())


@rich.repr.auto
class Formatted(abc.ABC):

    def _repr(self):
        to_print = self._prune()
        global RICH_CONSOLE
        RICH_CONSOLE.print(to_print)
        ret = RICH_CONSOLE.file.getvalue()
        RICH_CONSOLE.file.close()
        RICH_CONSOLE = Console(file=StringIO())
        # ToDO find more elegant way to flush this
        return ret

    def __repr__(self) -> str:
        return self._repr()

    def __str__(self) -> str:
        return self._repr()

    @abc.abstractmethod
    def _prune(self):
        raise NotImplemented


class FormattedBaseModel(Formatted, BaseModel):

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

    def _prune(self):
        dct = self._prune_dict(self.dict())
        config = {k: (self._prune_pydantic(self.model_fields[k].annotation, v),
                      self.model_fields[k].default) for k, v in dct.items()}
        return create_model(self.__class__.__name__, **config)(**dct)


class Prompt(FormattedBaseModel):
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


class DatasetEntry(FormattedBaseModel, extra=Extra.allow):
    prompt: Prompt
