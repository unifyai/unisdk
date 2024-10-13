from typing import List, Optional

from openai.types.chat import ChatCompletion as _ChatCompletion
from openai.types.chat.chat_completion import (
    ChatCompletionMessage as _ChatCompletionMessage,
)
from openai.types.chat.chat_completion import Choice as _Choice
from openai.types.completion_usage import CompletionUsage as _CompletionUsage

from ..base import _FormattedBaseModel


class ChatCompletionMessage(_FormattedBaseModel, _ChatCompletionMessage):
    pass


class Choice(_FormattedBaseModel, _Choice):
    # only override pydantic types  which require FormattedBaseModel
    message: ChatCompletionMessage


class CompletionUsage(_FormattedBaseModel, _CompletionUsage):
    # cost is an extra field we've added, not in the OpenAI standard
    # for local models, cost is None
    cost: Optional[float] = None


class ChatCompletion(_FormattedBaseModel, _ChatCompletion):
    # only override pydantic types  which require FormattedBaseModel
    choices: List[Choice]
    usage: Optional[CompletionUsage] = None

    def __init__(self, assistant_message: Optional[str] = None, **kwargs):
        """
        Create ChatCompletion instance.

        Args:
            assistant_message: The assistant message, optional.

        Returns:
            The pydantic ChatCompletion instance.
        """
        if assistant_message:
            kwargs = {
                **dict(
                    id="",
                    choices=[
                        Choice(
                            finish_reason="stop",
                            index=0,
                            message=ChatCompletionMessage(
                                role="assistant",
                                content=assistant_message,
                            ),
                        ),
                    ],
                    created=0,
                    model="",
                    object="chat.completion",
                    **kwargs,
                ),
                **kwargs,
            }
        super().__init__(**kwargs)
