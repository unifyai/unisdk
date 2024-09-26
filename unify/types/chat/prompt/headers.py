from pydantic import ConfigDict
from openai._types import Headers as _Headers

from ...base import _FormattedBaseModel


class Headers(_FormattedBaseModel, _Headers):
    model_config = ConfigDict(extra="forbid")
