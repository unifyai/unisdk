from pydantic import Extra
from typing import Union, Optional

from unify.agent import Agent
from unify.chat.clients import _Client
from unify.types import Prompt, Score, Datum, ChatCompletion


class Evaluation(Datum, extra=Extra.allow, arbitrary_types_allowed=True):
    prompt: Prompt
    response: ChatCompletion
    agent: Union[str, _Client, Agent]
    score: Score
    rationale: Optional[str]
