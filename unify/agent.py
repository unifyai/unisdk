import abc
from typing import Union

import unify
from unify.types import Prompt


class Agent(abc.ABC):

    def __init__(self):
        self.__call__ = unify.with_logging(
            self.__call__,
            endpoint=self.__class__.__name__,
        )

    @abc.abstractmethod
    def __call__(self, prompt: Union[str, Prompt]):
        raise NotImplemented
