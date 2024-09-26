from typing import Union
from typing_extensions import TypeAlias

from .response_format_text import *
from .response_format_json_object import *
from .response_format_json_schema import *
from . import response_format_text
from . import response_format_json_object
from . import response_format_json_schema

ResponseFormat: TypeAlias = Union[
    ResponseFormatText, ResponseFormatJSONObject, ResponseFormatJSONSchema
]
