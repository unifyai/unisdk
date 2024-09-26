from openai.types.chat.chat_completion import Choice as _Choice

from ....base import _FormattedBaseModel
from .chat_completion_message import *
from .choice_logprobs import *
from . import chat_completion_message
from . import choice_logprobs


class Choice(_FormattedBaseModel, _Choice):
    model_config = ConfigDict(extra="forbid")
    # only override pydantic types  which require FormattedBaseModel
    logprobs: Optional[ChoiceLogprobs] = None
    message: ChatCompletionMessage
