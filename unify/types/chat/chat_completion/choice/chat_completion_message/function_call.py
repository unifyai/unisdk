from pydantic import ConfigDict
from openai.types.chat.chat_completion_message import (
    FunctionCall as _FunctionCall)

from .....base import _FormattedBaseModel


class FunctionCall(_FormattedBaseModel, _FunctionCall):
    model_config = ConfigDict(extra="forbid")
    # no custom types
