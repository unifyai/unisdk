from pydantic import ConfigDict
from openai.types.completion_usage import CompletionUsage as _CompletionUsage

from ...base import _FormattedBaseModel


class CompletionUsage(_FormattedBaseModel, _CompletionUsage):
    model_config = ConfigDict(extra="forbid")
    # cost is an extra field we've added, not in the OpenAI standard
    cost: float
