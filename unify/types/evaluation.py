from __future__ import annotations
import abc
from pydantic import ConfigDict
from typing import Optional, Dict, Union

import unify
from .dataset import Datum

DEFAULT_CONFIG = {
    0.0: "bad",
    0.5: "good",
    0.8: "very good",
    1.0: "excellent"
}


class Score(Datum):
    model_config = ConfigDict(extra="forbid")
    value: Optional[float]
    description: str
    config: Dict[float, str]

    def __init__(
            self,
            value: Optional[float] = None,
            config: Optional[Dict[float, str]] = None
    ) -> None:
        """
        Create Score instance.

        Args:
            value: The value of the assigned score.

            config: The configuration for the score. Defaults to

        Returns:
            The pydantic Score instance, with associated value and class description
        """
        global DEFAULT_CONFIG
        if config is None:
            config = DEFAULT_CONFIG
        assert value is None or value in config, \
            "value {} passed is not a valid value, " \
            "based on the config for this Score class {}".format(value, config)
        super().__init__(
            value=value,
            description="Failed to parse judge response" if value is None
            else config[value],
            config=config
        )

    def __sub__(self, other: Union[Dict, Score, unify.Scores, float, int]):
        if isinstance(other, Score):
            other = other.value
        elif isinstance(other, unify.Scores):
            return self.value - other
        assert isinstance(other, float) or isinstance(other, int), \
            "other must either be numeric"
        return RelDiffScore(self.value - other)

    def __add__(self, other: Union[Dict, Score, unify.Scores, float, int]):
        if isinstance(other, Score):
            other = other.value
        elif isinstance(other, unify.Scores):
            return self.value + other
        assert isinstance(other, float) or isinstance(other, int), \
            "other must either be numeric"
        return RelDiffScore(self.value + other)

    def __rsub__(self, other: Union[Dict, float, int]):
        return self.__neg__().__add__(other)

    def __neg__(self):
        return RelDiffScore(-self.value)

    def __pos__(self):
        return self

    def __abs__(self):
        return RelDiffScore(abs(self.value))


class DiffConfig(dict, abc.ABC):

    def __init__(self, mode: str):
        assert mode in ("Relative", "L1"), "Invalid mode specified."
        self._mode = mode
        super().__init__()

    @staticmethod
    def _check_bounds(key: float):
        assert isinstance(key, float), (
            "Expected a float, but found {} of type {}".format(key, type(key)))
        assert -1. <= key <= 1., (
            "Expected value between 0. and 1., but found {}".format(key))

    def __setitem__(self, key: float, value: str):
        self._check_bounds(key)
        super().__setitem__(key, value)

    def __getitem__(self, key):
        self._check_bounds(key)
        return super().__getitem__(key)

    def __missing__(self, key):
        self.__setitem__(
            key, "The {} Difference between the two scores.".format(self._mode)
        )
        return self.__getitem__(key)

    def __contains__(self, key: float) -> bool:
        self._check_bounds(key)
        self.__setitem__(
            key, "The {} Difference between the two scores.".format(self._mode)
        )
        return True


class RelDiffConfig(DiffConfig):

    def __init__(self):
        super().__init__("Relative")


class L1DiffConfig(DiffConfig):

    def __init__(self):
        super().__init__("L1")


class RelDiffScore(Score):

    def __init__(self, value: Optional[float] = None) -> None:
        super().__init__(value=value, config=RelDiffConfig())


class L1DiffScore(Score):

    def __init__(self, value: Optional[float] = None) -> None:
        super().__init__(value=value, config=L1DiffConfig())
