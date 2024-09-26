from typing import List
from pydantic import ConfigDict
from openai.types.chat.chat_completion import (
    ChatCompletionTokenLogprob as _ChatCompletionTokenLogprob)

from ......base import _FormattedBaseModel
from .top_logprob import TopLogprob


class ChatCompletionTokenLogprob(_FormattedBaseModel, _ChatCompletionTokenLogprob):
    model_config = ConfigDict(extra="forbid")
    # only override pydantic types  which require FormattedBaseModel
    top_logprobs: List[TopLogprob]
