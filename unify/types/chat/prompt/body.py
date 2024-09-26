from pydantic import ConfigDict
from openai._types import Body as _Body

from ...base import _FormattedBaseModel


class Body(_FormattedBaseModel, _Body):
    model_config = ConfigDict(extra="forbid")
