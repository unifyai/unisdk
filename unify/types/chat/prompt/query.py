from pydantic import ConfigDict
from openai._types import Query as _Query

from ...base import _FormattedBaseModel


class Query(_FormattedBaseModel, _Query):
    model_config = ConfigDict(extra="forbid")
