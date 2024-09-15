from typing import Union

from unify.agent import Agent
from unify.chat.clients import _Client
from unify.types import Datum, Score, _FormattedBaseModel, ChatCompletion


class Evaluation(_FormattedBaseModel, arbitrary_types_allowed=True):
    datum: Datum
    response: ChatCompletion
    agent: Union[str, _Client, Agent]
    score: Score
