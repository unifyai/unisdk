from pydantic import Extra, BaseModel
from typing import Union, Optional, List, Dict, Type

from unify.agent import Agent
from unify.dataset import Dataset
from unify.chat.clients import _Client, _UniLLMClient
from unify.types import Prompt, Score, Datum, ChatCompletion


class ScoreSet(Dataset):

    def __init__(
            self,
            scores: Union[Score, List[Score]],
            *,
            scorer: Type[Score],
            name: str = None,
            auto_sync: Union[bool, str] = False,
            api_key: Optional[str] = None
    ) -> None:
        if not isinstance(scores, list):
            scores = [scores]
        assert all(type(s) is type(scores[0]) for s in scores), \
            "All scores passed to a ScoreSet must be of the same type."
        self._score_count = {
            val: (desc, len([s for s in scores if s.value == val]))
            for val, desc in scores[0].config.items()
        }
        self._scorer_name = scorer.__name__
        super().__init__(
            data=scores,
            name=name,
            auto_sync=auto_sync,
            api_key=api_key
        )

    def __rich_repr__(self) -> Dict:
        """
        Used by the rich package for representing and print the instance.
        """
        yield {
            "scorer": self._scorer_name,
            "counts": self._score_count
        }


class Evaluation(Datum, extra=Extra.allow, arbitrary_types_allowed=True):
    prompt: Prompt
    response: ChatCompletion
    agent: Union[str, _Client, Agent]
    score: Score
    evaluator: Optional[str] = None
    rationale: Optional[Union[str, Dict, BaseModel]] = None


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
        scorer = type(evaluations[0].score)
        self._class_config = evaluations[0].score.config

        # extract the shared data
        shared_data = dict()
        for field in Evaluation.model_fields:
            if all(getattr(e, field) == getattr(evaluations[0], field)
                   for e in evaluations):
                val = getattr(evaluations[0], field)
                if isinstance(val, BaseModel):
                    val = val.model_dump()
                elif isinstance(val, _UniLLMClient):
                    val = val.endpoint
                shared_data[field] = val

        valid_scores = [e.score.value for e in evaluations if e.score.value is not None]
        self._mean_score = sum(valid_scores) / len(valid_scores)
        self._score_set = ScoreSet([e.score for e in evaluations], scorer=scorer)

        super().__init__(
            data=evaluations,
            name=name,
            auto_sync=auto_sync,
            shared_data=shared_data,
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

    # noinspection PyTypeChecker
    @property
    def score_set(self) -> ScoreSet:
        return self._score_set
