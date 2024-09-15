import abc
from typing import Union

import unify
from unify.types import Prompt


class Agent(abc.ABC):

    def __init__(self):
        self._call = unify.with_logging(self._call, endpoint=self.__class__.__name__)

    @abc.abstractmethod
    def _call(self, prompt: Union[str, Prompt]):
        raise NotImplemented

    @abc.abstractmethod
    def __call__(self, prompt: Union[str, Prompt]):
        return self._call(**prompt.dict())
