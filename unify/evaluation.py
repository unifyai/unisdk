from __future__ import annotations
import copy
from pydantic import Extra, BaseModel
from typing import Union, Optional, List, Dict, Type

from unify.agent import Agent
from unify.dataset import Dataset
from unify.chat.clients import _Client
from unify.types import (_Formatted, Prompt, Score, RelDiffScore, L1DiffScore, Datum,
                         ChatCompletion)


class Scores(dict, _Formatted):

    def __init__(
            self,
            dct: Optional[Dict[str, Score]] = None,
            **scores: Optional[Dict[str, Score]]
    ) -> None:
        if dct is None:
            dct = dict(**scores)
        self._data = dct
        score0 = list(dct.values())[0]
        self._config = score0.config
        super().__init__(dct)

    def __sub__(self, other: Union[Dict, Score, float, int]):
        if isinstance(other, dict):
            return Scores({k: RelDiffScore(v.value - other[k].value)
                           for k, v in self._data.items()})
        if isinstance(other, Score):
            other = other.value
        assert isinstance(other, float) or isinstance(other, int), \
            "other must either be a dict or must be numeric"
        return Scores({k: RelDiffScore(v.value - other.value)
                       for k, v in self._data.items()})

    def __add__(self, other: Union[Dict, Score, float, int]):
        if isinstance(other, dict):
            return Scores({k: RelDiffScore(v.value + other[k].value)
                           for k, v in self._data.items()})
        if isinstance(other, Score):
            other = other.value
        assert isinstance(other, float) or isinstance(other, int), \
            "other must either be a dict or must be numeric"
        return Scores({k: RelDiffScore(v.value + other)
                       for k, v in self._data.items()})

    def __rsub__(self, other: Union[Dict, float, int]):
        return self.__neg__().__add__(other)

    def __neg__(self):
        return Scores({k: -v for k, v in self._data.items()})

    def __pos__(self):
        return self

    def __abs__(self):
        return Scores({k: abs(v) for k, v in self._data.items()})

    def __rich_repr__(self) -> Dict:
        """
        Used by the rich package for representing and print the instance.
        """
        if len(self._config) == 1:
            config = {float: list(self._config.values())[0]}
        else:
            config = self._config
        yield "config", config
        yield {k: v.value for k, v in self._data.items()}


class Rationales(dict, _Formatted):

    def __init__(
            self,
            dct: Optional[Dict[str, str]] = None,
            **rationales: Optional[Dict[str, str]]
    ) -> None:
        if dct is None:
            dct = dict(**rationales)
        self._data = dct
        super().__init__(dct)

    def __rich_repr__(self) -> Dict:
        """
        Used by the rich package for representing and print the instance.
        """
        yield self._data


class Evaluation(Datum, extra=Extra.allow, arbitrary_types_allowed=True):
    prompt: Prompt
    response: ChatCompletion
    agent: Union[str, _Client, Agent]
    # score: Union[Score, Scores]
    # ToDo work out why above fails the pydantic_validator when passing Scores,
    #  but the below line does not.
    score: Optional[Union[Scores, Score]]
    scorer: Type[Score]
    evaluator: Optional[str] = None
    # rationale: Optional[Union[str, Rationales]] = None
    # ToDo work out why above fails the pydantic_validator when passing Rationales,
    #  but the below line does not.
    rationale: Optional[Union[Rationales, str]] = None

    def __add__(self, other):
        if other == 0:
            return self
        return (EvaluationSet(self) +
                (other if isinstance(other, EvaluationSet) else EvaluationSet(other)))

    def __sub__(self, other):
        return EvaluationSet(self) -\
               (other if isinstance(other, EvaluationSet) else EvaluationSet(other))

    def __radd__(self, other):
        if other == 0:
            return self
        return ((other if isinstance(other, EvaluationSet) else EvaluationSet(other)) +
                EvaluationSet(self))

    def __rsub__(self, other):
        return (other if isinstance(other, EvaluationSet) else EvaluationSet(other)) -\
               EvaluationSet(self)


# noinspection PyTypeChecker
class EvaluationSet(Dataset):

    def __init__(
            self,
            evaluations: Union[Evaluation, List[Evaluation]],
            *,
            name: str = None,
            auto_sync: Union[bool, str] = False,
            api_key: Optional[str] = None
    ) -> None:
        if isinstance(evaluations, Evaluation):
            evaluations = [evaluations]
        consistency_msg = \
            "All evaluations passed to an EvaluationSet must shared the same {}."
        # agent
        assert all(e.agent == evaluations[0].agent for e in evaluations), (
            consistency_msg.format("agent"))
        self._agent = evaluations[0].agent
        # scorer
        assert all(e.scorer is evaluations[0].scorer for e in evaluations), (
            consistency_msg.format("scorer"))
        self._scorer = evaluations[0].scorer
        # evaluator
        assert all(e.evaluator == evaluations[0].evaluator for e in evaluations), (
            consistency_msg.format("evaluator"))
        self._evaluator = evaluations[0].evaluator

        # shared data
        shared_data = {
            "agent": self._agent,
            "scorer": self._scorer,
            "evaluator": self._evaluator
        }

        # prompt
        if all(e.prompt == evaluations[0].prompt for e in evaluations):
            val = evaluations[0].prompt
            self._prompt = val
            if isinstance(val, BaseModel):
                val = val.model_dump()
            shared_data["prompt"] = val
        else:
            self._prompt = [e.prompt for e in evaluations]
        # response
        if all(e.response == evaluations[0].response for e in evaluations):
            val = evaluations[0].response
            self._response = val
            if isinstance(val, BaseModel):
                val = val.model_dump()
            shared_data["response"] = val
        else:
            self._response = [e.response for e in evaluations]
        # score
        if isinstance(evaluations[0].score, dict):
            self._score = [Scores(e.score) for e in evaluations]
            valid_scores = [
                score.value for evl in evaluations for score in evl.score.values()
                if score is not None
            ]
        else:
            self._score = [e.score for e in evaluations]
            valid_scores = [s.value for s in self._score if s is not None]
        # rationale
        if isinstance(evaluations[0].rationale, dict):
            self._rationale = [Rationales(e.rationale) for e in evaluations]
        else:
            self._rationale = [e.rationale for e in evaluations]

        # reductions
        self._mean_score = sum(valid_scores) / len(valid_scores)
        self._score_freq = {
            k: valid_scores.count(k) for k in sorted(list(set(valid_scores)))
        }

        super().__init__(
            data=evaluations,
            name=name,
            auto_sync=auto_sync,
            shared_data=shared_data,
            api_key=api_key
        )

    # Properties

    @property
    def prompt(self) -> Union[Prompt, List[Prompt]]:
        return self._prompt

    @property
    def response(self) -> Union[ChatCompletion, List[ChatCompletion]]:
        return self._response

    @property
    def agent(self) -> Union[str, _Client, Agent]:
        return self._agent

    @property
    def score(self) -> List[Score]:
        return self._score

    @property
    def evaluator(self) -> Union[str, List[str]]:
        return self._evaluator

    @property
    def rationale(self) -> List[str]:
        return self._rationale

    @property
    def scorer(self) -> Type[Score]:
        return self._scorer

    @property
    def mean_score(self) -> float:
        return self._mean_score

    @property
    def score_freq(self) -> Dict[float, int]:
        return self._score_freq

    def __add__(self, other):
        if other == 0:
            return self
        dataset = super().__add__(
            EvaluationSet(other) if not isinstance(other, EvaluationSet) else other
        )
        return EvaluationSet(
            dataset._data,
            name=self._name,
            auto_sync=self._auto_sync_flag,
            api_key=self._api_key
        )

    def __sub__(self, other):
        if other == 0:
            return self
        dataset = super().__sub__(
            EvaluationSet(other) if not isinstance(other, EvaluationSet) else other
        )
        return EvaluationSet(
            dataset._data,
            name=self._name,
            auto_sync=self._auto_sync_flag,
            api_key=self._api_key
        )

    def __radd__(self, other):
        if other == 0:
            return self
        dataset = super().__radd__(
            EvaluationSet(other) if not isinstance(other, EvaluationSet) else other
        )
        return EvaluationSet(
            dataset._data,
            name=self._name,
            auto_sync=self._auto_sync_flag,
            api_key=self._api_key
        )

    def __rsub__(self, other):
        dataset = super().__rsub__(
            EvaluationSet(other) if not isinstance(other, EvaluationSet) else other
        )
        return EvaluationSet(
            dataset._data,
            name=self._name,
            auto_sync=self._auto_sync_flag,
            api_key=self._api_key
        )

    def score_diff(
            self,
            other: EvaluationSet,
            agent: Union[str, _Client, Agent],
            mode: str = "relative"
    ) -> EvaluationSet:
        assert mode in ("relative", "l1"), "Invalid mode specified."
        if mode == "relative":
            scores = [s.score - o.score for s, o in zip(self._data, other._data)]
        else:
            scores = [abs(s.score - o.score) for s, o in zip(self._data, other._data)]
        data = [copy.copy(d) for d in self._data]
        for d, s in zip(data, scores):
            d.score = s
            d.scorer = {
                "relative": RelDiffScore,
                "l1": L1DiffScore
            }[mode]
            d.agent = agent
        return EvaluationSet(
            data,
            name=self._name,
            auto_sync=self._auto_sync_flag,
            api_key=self._api_key
        )
