from __future__ import annotations
import copy
from pydantic import Extra, BaseModel
from typing_extensions import Self
from typing import Union, Optional, List, Dict, Any

import unify
from unify.agent import Agent
from unify.dataset import Dataset
from unify.chat.clients import _Client
from unify.types import _Formatted, Score, RelDiffScore, L1DiffScore, Datum, \
    ChatCompletion


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
    datum: Datum
    response: ChatCompletion
    agent: Union[str, _Client, Agent]
    # score: Union[Score, Scores]
    # ToDo work out why above fails the pydantic_validator when passing Scores,
    #  but the below line does not.
    score: Optional[Union[Scores, Score]]
    evaluator: Optional[Any] = None  # << ToDo fix this circular import error
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
            evaluator: Optional[str, unify.Evaluator] = None,
            name: str = None,
            api_key: Optional[str] = None
    ) -> None:
        if isinstance(evaluations, Evaluation):
            evaluations = [evaluations]
        consistency_msg = \
            "All evaluations passed to an EvaluationSet must share the same {}."
        # agent
        assert all(e.agent == evaluations[0].agent for e in evaluations), (
            consistency_msg.format("agent"))
        self._agent = evaluations[0].agent
        # evaluator
        assert all(e.evaluator == evaluations[0].evaluator for e in evaluations), (
            consistency_msg.format("evaluator"))
        if evaluator is not None:
            self._evaluator = evaluator
        else:
            self._evaluator = evaluations[0].evaluator

        # shared data
        shared_data = {
            "agent": self._agent,
            "evaluator": self._evaluator
        }

        # datum
        if all(e.datum == evaluations[0].datum for e in evaluations):
            val = evaluations[0].datum
            self._datum = val
            if isinstance(val, BaseModel):
                val = val.model_dump()
            shared_data["datum"] = val
        else:
            self._datum = [e.datum for e in evaluations]
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
            shared_data=shared_data,
            api_key=api_key
        )

    # Properties

    @property
    def datum(self) -> Union[Datum, List[Datum]]:
        return self._datum

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
    def evaluator(self) -> Union[Any, List[Any]]:  # << ToDo fix this circular import
        return self._evaluator

    @property
    def rationale(self) -> List[str]:
        return self._rationale

    @property
    def mean_score(self) -> float:
        return self._mean_score

    @property
    def score_freq(self) -> Dict[float, int]:
        return self._score_freq

    # Setters

    def set_evaluator(self, evaluator: unify.Evaluator) -> Self:
        self._evaluator = evaluator
        return self

    # Dunders

    def __add__(self, other):
        if other == 0:
            return self
        dataset = super().__add__(
            EvaluationSet(other) if not isinstance(other, EvaluationSet) else other
        )
        return EvaluationSet(
            dataset._data,
            name=self._name,
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
            api_key=self._api_key
        )

    def __rsub__(self, other):
        dataset = super().__rsub__(
            EvaluationSet(other) if not isinstance(other, EvaluationSet) else other
        )
        return EvaluationSet(
            dataset._data,
            name=self._name,
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
            d.score_config = {
                "relative": RelDiffScore,
                "l1": L1DiffScore
            }[mode]().config
            d.agent = agent
        return EvaluationSet(
            data,
            name=self._name,
            api_key=self._api_key
        )

    def _upload_dataset(self, dataset_name: Optional[str]):
        dataset_name = "" if dataset_name is None else dataset_name
        if dataset_name not in unify.list_datasets() and dataset_name != "":
            unify.upload_dataset_from_dictionary(
                dataset_name, [unify.Datum(p).model_dump() for p in self.datum]
            )
        else:
            data_to_upload = list()
            for datum in self.datum:
                if datum._id is None:
                    data_to_upload.append(datum.model_dump())
            unify.add_data_by_value(dataset_name, data_to_upload)

    @staticmethod
    def _upload_evaluator(evaluator: Optional[unify.Evaluator]):
        if evaluator is None or not isinstance(evaluator, unify.Evaluator):
            raise Exception(
                "Evaluator must be set in order to upload evaluations. You should call "
                ".set_evaluator() and pass the evaluator used to generate the "
                "evaluation.")
        if evaluator.name not in unify.list_evaluators():
            evaluator.upload()
        assert evaluator.name in unify.list_evaluators()

    def upload(
            self,
            dataset_name: str = "",
            evaluator: Optional[unify.Evaluator] = None
    ) -> Self:
        """
        Uploads the evaluation set to the console.

        Args:
            dataset_name: Optional name of the dataset to save (or synchronize) the data
            with upstream.

            evaluator: Optional evaluator to associate with this evaluation.
            If not passed, then the evaluator property is used. If this is unset, you
            should set it using set_evaluator().
        """
        self._upload_dataset(dataset_name)
        evaluator = evaluator if evaluator is not None else self._evaluator
        self._upload_evaluator(evaluator)
        unify.upload_evaluations(
            evaluator=evaluator.name,
            agent=self.agent,
            evaluations=[
                {
                    k: d.datum._id if k=="datum" else v
                    for k, v in d.model_dump().items()
                 }
                for d in self._data
            ],
        )
        return self

    def download(
            self,
            dataset_name: str = "",
            evaluator: Optional[unify.Evaluator] = None,
            overwrite: bool = False,
    ) -> Self:
        """
        Downloads all evaluations for the specified evaluator, dataset and agent
        locally.

        Args:
            dataset_name: Optional name of the dataset to save (or synchronize) the data
            with upstream.

            evaluator: Optional evaluator to associate with this evaluation.
            If not passed, then the evaluator property is used. If this is unset, you
            should set it using set_evaluator().

            overwrite: Whether to overwrite the local evaluations for any duplicates.
        """
        self._upload_dataset(dataset_name)
        evaluator = evaluator if evaluator is not None else self._evaluator
        self._upload_evaluator(evaluator)
        data = unify.get_evaluations(
            dataset=self.datum,
            agent=self.agent,
            evaluator=evaluator
        )
        if overwrite:
            unique_local = [item for item in self._data if item not in data]
            self._data = data + unique_local
        else:
            unique_upstream = [item for item in data if item not in self._data]
            self._data = self._data + unique_upstream
        return self

    def sync(self) -> Self:
        """
        Synchronize the dataset in both directions, downloading any values missing
        locally, and uploading any values missing from upstream in the account.

        Returns:
            This evaluation set after the in-place sync, useful for chaining methods.
        """
        self.download()
        self.upload()
        return self
