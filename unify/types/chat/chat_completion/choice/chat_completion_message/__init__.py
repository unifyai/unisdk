from pydantic import ConfigDict
from typing import Optional, List
from openai.types.chat.chat_completion import (
    ChatCompletionMessage as _ChatCompletionMessage)

from .....base import _FormattedBaseModel
from .function_call import FunctionCall
from .chat_completion_message_tool_call import ChatCompletionMessageToolCall


class ChatCompletionMessage(_FormattedBaseModel, _ChatCompletionMessage):
    model_config = ConfigDict(extra="forbid")
    # only override pydantic types  which require FormattedBaseModel
    function_call: Optional[FunctionCall] = None
    tool_calls: Optional[List[ChatCompletionMessageToolCall]] = None
    # no more custom types
