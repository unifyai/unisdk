from pydantic import ConfigDict
from openai.types.chat.chat_completion import (
    ChatCompletionMessage as _ChatCompletionMessage)

from ....base import _FormattedBaseModel


class ChatCompletionMessage(_FormattedBaseModel, _ChatCompletionMessage):
    model_config = ConfigDict(extra="forbid")
