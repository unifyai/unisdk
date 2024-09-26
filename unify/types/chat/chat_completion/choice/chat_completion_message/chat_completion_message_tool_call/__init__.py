from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall as _ChatCompletionMessageToolCall)

from ......base import _FormattedBaseModel
from .function import *
from . import function


class ChatCompletionMessageToolCall(
    _FormattedBaseModel, _ChatCompletionMessageToolCall
):
    model_config = ConfigDict(extra="forbid")
    # only override pydantic types  which require FormattedBaseModel
    function: Function
    # no more custom types
