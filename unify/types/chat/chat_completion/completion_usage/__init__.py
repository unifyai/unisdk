from typing import Optional
from pydantic import ConfigDict
from openai.types.completion_usage import \
    (CompletionUsage as _CompletionUsage,
     CompletionTokensDetails as _CompletionTokensDetails)

from ....base import _FormattedBaseModel


class CompletionTokensDetails(_FormattedBaseModel, _CompletionTokensDetails):
    model_config = ConfigDict(extra="forbid")


class CompletionUsage(_FormattedBaseModel, _CompletionUsage):
    model_config = ConfigDict(extra="forbid")
    # only override pydantic types  which require FormattedBaseModel
    completion_tokens_details: Optional[CompletionTokensDetails] = None
    # cost is an extra field we've added, not in the OpenAI standard
    cost: float
