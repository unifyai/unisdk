from typing import Union
from pydantic import Extra

from unify.agent import Agent
from unify.chat.clients import _Client
from unify.types import Prompt, Score, _FormattedBaseModel, ChatCompletion


class Evaluation(_FormattedBaseModel, extra=Extra.allow, arbitrary_types_allowed=True):
    prompt: Prompt
    response: ChatCompletion
    agent: Union[str, _Client, Agent]
    score: Score
