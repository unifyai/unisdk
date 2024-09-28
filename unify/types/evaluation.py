import abc
from pydantic import ConfigDict
from typing import Optional, Dict, Union, List

import unify
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


class ScoreSet(unify.Dataset):

    def __init__(
            self,
            scores: Union[Score, List[Score]],
            *,
            name: str = None,
            auto_sync: Union[bool, str] = False,
            api_key: Optional[str] = None
    ) -> None:
        if not isinstance(scores, list):
            scores = [scores]
        assert all(type(s) is type(scores[0]) for s in scores), \
            "All scores passed to a ScoreSet must be of the same type."
        self._class_config = scores[0].config

        super().__init__(
            data=scores,
            name=name,
            auto_sync=auto_sync,
            api_key=api_key
        )
