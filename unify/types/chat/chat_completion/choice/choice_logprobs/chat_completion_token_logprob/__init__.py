from typing import List
from openai.types.chat.chat_completion import (
    ChatCompletionTokenLogprob as _ChatCompletionTokenLogprob)
from pydantic import ConfigDict
from openai.types.chat.chat_completion_token_logprob import TopLogprob as _TopLogprob

from ......base import _FormattedBaseModel


class TopLogprob(_FormattedBaseModel, _TopLogprob):
    model_config = ConfigDict(extra="forbid")
    # no custom types


class ChatCompletionTokenLogprob(_FormattedBaseModel, _ChatCompletionTokenLogprob):
    model_config = ConfigDict(extra="forbid")
    # only override pydantic types  which require FormattedBaseModel
    top_logprobs: List[TopLogprob]
