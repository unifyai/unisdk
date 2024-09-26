from typing import Union
from typing_extensions import TypeAlias

from .chat_completion_assistant_message_param import *
from .chat_completion_function_message_param import *
from .chat_completion_system_message_param import *
from .chat_completion_tool_message_param import *
from .chat_completion_user_message_param import *
from . import chat_completion_assistant_message_param
from . import chat_completion_function_message_param
from . import chat_completion_system_message_param
from . import chat_completion_tool_message_param
from . import chat_completion_user_message_param

ChatCompletionMessageParam: TypeAlias = Union[
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionFunctionMessageParam,
]
