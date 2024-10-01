import abc
from pydantic import ConfigDict
from typing import Optional, Dict

from .dataset import Datum


class Score(Datum, abc.ABC):
    model_config = ConfigDict(extra="forbid")
    value: Optional[float]
    description: str

    def __init__(self, value: Optional[float] = None):
        """
        Create Score instance.

        Args:
            value: The value of the assigned score

        Returns:
            The pydantic Score instance, with associated value and class description
        """
        assert value in self.config or value is None, \
            "value {} passed is not a valid value, " \
            "based on the config for this Score class {}".format(value, self.config)
        super().__init__(
            value=value,
            description="Failed to parse judge response" if value is None
            else self.config[value]
        )

    @property
    @abc.abstractmethod
    def config(self) -> Dict[float, str]:
        raise NotImplementedError


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

    @property
    def config(self) -> Dict[float, str]:
        return RelDiffConfig()


class L1DiffScore(Score):

    @property
    def config(self) -> Dict[float, str]:
        return L1DiffConfig()
