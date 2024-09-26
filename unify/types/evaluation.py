import abc
from pydantic import ConfigDict
from typing import Optional, Dict

from .types import _FormattedBaseModel


class Score(_FormattedBaseModel, abc.ABC):
    model_config = ConfigDict(extra="forbid")
    value: float
    description: str

    def __init__(self, value: Optional[float] = None):
        """
        Create Score instance.

        Args:
            value: The value of the assigned score

        Returns:
            The pydantic Score instance, with associated value and class description
        """
        value = 0. if value is None else value
        assert value in self.config, \
            "value {} passed is not a valid value, " \
            "based on the config for this Score class {}".format(value, self.config)
        super().__init__(value=value, description=self.config[value])

    @property
    @abc.abstractmethod
    def config(self) -> Dict[float, str]:
        raise NotImplementedError
