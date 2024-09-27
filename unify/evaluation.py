from pydantic import Extra
from typing import Union, Optional, List

from unify.agent import Agent
from unify.dataset import Dataset
from unify.chat.clients import _Client
from unify.types import Prompt, Score, Datum, ChatCompletion


class Evaluation(Datum, extra=Extra.allow, arbitrary_types_allowed=True):
    prompt: Prompt
    response: ChatCompletion
    agent: Union[str, _Client, Agent]
    score: Score
    rationale: Optional[str]


class EvaluationSet(Dataset):

    def __init__(
            self,
            data: Union[Evaluation, List[Evaluation]],
            *,
            name: str = None,
            auto_sync: Union[bool, str] = False,
            api_key: Optional[str] = None,
    ) -> None:
        super().__init__(
            data=data,
            name=name,
            auto_sync=auto_sync,
            api_key=api_key
        )
