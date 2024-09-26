from pydantic import ConfigDict
from typing import Optional, List
from openai.types.chat.chat_completion import (
    ChoiceLogprobs as _ChoiceLogprobs)

from .....base import _FormattedBaseModel
from .chat_completion_token_logprob import ChatCompletionTokenLogprob


class ChoiceLogprobs(_FormattedBaseModel, _ChoiceLogprobs):
    model_config = ConfigDict(extra="forbid")
    # only override pydantic types  which require FormattedBaseModel
    content: Optional[List[ChatCompletionTokenLogprob]] = None
    refusal: Optional[List[ChatCompletionTokenLogprob]] = None
