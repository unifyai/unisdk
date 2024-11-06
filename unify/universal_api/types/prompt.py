from typing import Dict, List, Mapping, Optional, Union

import unify
from openai._types import Body, Query
from openai.types.chat import (
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
)
from openai.types.chat.completion_create_params import ResponseFormat
from pydantic import BaseModel, Extra


class Prompt(BaseModel, extra=Extra.allow):
    messages: Optional[List[Dict]] = None
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
        **kwargs,
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
            kwargs["messages"] = [
                {"content": system_message, "role": "system"},
            ] + kwargs["messages"]
        if user_message:
            kwargs["messages"] += [{"content": user_message, "role": "user"}]
        if not kwargs["messages"]:
            kwargs["messages"] = None
        super().__init__(**kwargs)

    def __add__(self, other):
        if other == 0:
            return self
        return unify.Dataset(self) + (
            other if isinstance(other, unify.Dataset) else unify.Dataset(other)
        )

    def __sub__(self, other):
        return unify.Dataset(self) - (
            other if isinstance(other, unify.Dataset) else unify.Dataset(other)
        )

    def __radd__(self, other):
        if other == 0:
            return self
        return (
            other if isinstance(other, unify.Dataset) else unify.Dataset(other)
        ) + unify.Dataset(self)

    def __rsub__(self, other):
        return (
            other if isinstance(other, unify.Dataset) else unify.Dataset(other)
        ) - unify.Dataset(self)

    def __hash__(self):
        return hash(str(self))
