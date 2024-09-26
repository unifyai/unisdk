from pydantic import ConfigDict
from openai.types.chat.chat_completion_message_tool_call import (
    Function as _Function)

from ......base import _FormattedBaseModel


class Function(_FormattedBaseModel, _Function):
    model_config = ConfigDict(extra="forbid")
    # no custom types
