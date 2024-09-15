from typing import Union
from openai.types.chat.chat_completion import ChatCompletion

from unify.agent import Agent
from unify.chat.clients import _Client
from unify.types import Datum, Score, _FormattedBaseModel


class Evaluation(_FormattedBaseModel, arbitrary_types_allowed=True):
    datum: Datum
    response: ChatCompletion
    agent: Union[str, _Client, Agent]
    score: Score
