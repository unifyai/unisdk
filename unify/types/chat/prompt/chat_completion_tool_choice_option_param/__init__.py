from typing import Union, Literal
from typing_extensions import TypeAlias

from .chat_completion_named_tool_choice_param import ChatCompletionNamedToolChoiceParam

ChatCompletionToolChoiceOptionParam: TypeAlias = Union[
    Literal["none", "auto", "required"], ChatCompletionNamedToolChoiceParam
]
