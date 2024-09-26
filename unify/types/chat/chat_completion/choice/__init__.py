from pydantic import ConfigDict
from openai.types.chat.chat_completion import Choice as _Choice
from openai.types.chat.chat_completion import (
    ChatCompletionMessage as _ChatCompletionMessage)

from ....base import _FormattedBaseModel


class ChatCompletionMessage(_FormattedBaseModel, _ChatCompletionMessage):
    model_config = ConfigDict(extra="forbid")
    # no custom types


class Choice(_FormattedBaseModel, _Choice):
    model_config = ConfigDict(extra="forbid")
    # only override pydantic types  which require FormattedBaseModel
    message: ChatCompletionMessage
