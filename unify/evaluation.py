from pydantic import Extra
from typing import Union, Optional, List, Dict

from unify.agent import Agent
from unify.dataset import Dataset
from unify.chat.clients import _Client
from unify.types import Prompt, Score, Datum, ChatCompletion


class Evaluation(Datum, extra=Extra.allow, arbitrary_types_allowed=True):
    prompt: Prompt
    response: ChatCompletion
    agent: Union[str, _Client, Agent]
    score: Score
    evaluator: Optional[str] = None
    rationale: Optional[str] = None


class EvaluationSet(Dataset):

    def __init__(
            self,
            evaluations: Union[Evaluation, List[Evaluation]],
            *,
            name: str = None,
            auto_sync: Union[bool, str] = False,
            api_key: Optional[str] = None
    ) -> None:
        if not isinstance(evaluations, list):
            evaluations = [evaluations]
        consistency_msg = \
            "All evaluations passed to an EvaluationSet must shared the same {}."
        assert all(e.agent == evaluations[0].agent for e in evaluations), (
            consistency_msg.format("agent"))
        self._agent = evaluations[0].agent
        assert all(e.score.config == evaluations[0].score.config
                   for e in evaluations), consistency_msg.format("class_config")
        self._class_config = evaluations[0].score.config
        valid_scores = [e.score.value for e in evaluations if e.score.value is not None]
        self._mean_score = sum(valid_scores)/len(valid_scores)
        self._score_distribution =\
            {
                k: sum([e.score.value == k for e in evaluations])
                for k in self._class_config.keys()
            }

        super().__init__(
            data=evaluations,
            name=name,
            auto_sync=auto_sync,
            api_key=api_key
        )

    # Properties

    @property
    def agent(self) -> Union[str, _Client, Agent]:
        return self._agent

    @property
    def class_config(self) -> Dict[float, str]:
        return self._class_config

    @property
    def mean_score(self) -> float:
        return self._mean_score

    @property
    def score_distribution(self) -> Dict[float, int]:
        return self._score_distribution


class LLMJuryEvaluationSet(EvaluationSet):

    def __init__(
            self,
            evaluations: Union[Evaluation, List[Evaluation]],
            *,
            name: str = None,
            auto_sync: Union[bool, str] = False,
            api_key: Optional[str] = None
    ) -> None:
        self._judge_score_distribution =\
            {
                k: [e.evaluator.name for e in evaluations]
                for k in self._class_config.keys()
            }
        super().__init__(
            evaluations=evaluations,
            name=name,
            auto_sync=auto_sync,
            api_key=api_key
        )

    # Properties

    @property
    def judge_score_distribution(self) -> Dict[float, List[str]]:
        return self._judge_score_distribution
