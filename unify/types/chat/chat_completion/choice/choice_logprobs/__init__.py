from typing import Optional
from openai.types.chat.chat_completion import (
    ChoiceLogprobs as _ChoiceLogprobs)

from .....base import _FormattedBaseModel
from .chat_completion_token_logprob import *
from . import chat_completion_token_logprob


class ChoiceLogprobs(_FormattedBaseModel, _ChoiceLogprobs):
    model_config = ConfigDict(extra="forbid")
    # only override pydantic types  which require FormattedBaseModel
    content: Optional[List[ChatCompletionTokenLogprob]] = None
    refusal: Optional[List[ChatCompletionTokenLogprob]] = None
