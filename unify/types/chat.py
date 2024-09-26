from pydantic import ConfigDict
from typing import Optional, Union, List, Dict, Mapping
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
from .base import _FormattedBaseModel


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
