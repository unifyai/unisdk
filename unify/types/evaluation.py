import abc
from pydantic import ConfigDict
from typing import Optional, Dict

from .base import _FormattedBaseModel


class Score(_FormattedBaseModel, abc.ABC):
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
