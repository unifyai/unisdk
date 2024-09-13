import json
from pydantic import BaseModel, Extra
from typing import Optional, Union, List, Dict, Mapping
from openai.types.chat import (
    ChatCompletionToolParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionMessageParam,
)
from openai._types import Headers, Query, Body
from openai.types.chat.completion_create_params import ResponseFormat


class FormattedBaseModel(BaseModel):

    def __repr__(self) -> str:
        dct = {k: v for k, v in self.dict().items() if v is not None}
        return self.__class__.__name__ + "({})".format(json.dumps(dct, indent=4)[1:-1])

    def __str__(self) -> str:
        return self.__repr__()


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
