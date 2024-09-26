from openai.types.chat import ChatCompletion as _ChatCompletion

from ...base import _FormattedBaseModel
from .choice import *
from .completion_usage import *
from . import choice
from . import completion_usage


class ChatCompletion(_FormattedBaseModel, _ChatCompletion):
    model_config = ConfigDict(extra="forbid")
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
                                content=assistant_message
                            )
                        )
                    ],
                    created=0,
                    model="",
                    object="chat.completion",
                    **kwargs
                ),
                **kwargs
            }
        super().__init__(**kwargs)
