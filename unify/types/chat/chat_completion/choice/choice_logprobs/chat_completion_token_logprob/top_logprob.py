from pydantic import ConfigDict
from openai.types.chat.chat_completion_token_logprob import TopLogprob as _TopLogprob

from ......base import _FormattedBaseModel


class TopLogprob(_FormattedBaseModel, _TopLogprob):
    model_config = ConfigDict(extra="forbid")
