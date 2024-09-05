import abc
from typing import Union

import unify
from unify.chat import Prompt


class Agent(abc.ABC):

    @abc.abstractmethod
    def _call(self, prompt: Union[str, Prompt]):
        raise NotImplemented

    @abc.abstractmethod
    def __call__(self, prompt: Union[str, Prompt]):
        return unify.log(self._call(unify.handle_query(prompt)))
