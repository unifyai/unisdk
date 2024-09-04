import abc
from typing import Union
from openai.types.chat.chat_completion import ChatCompletion


import unify


class Agent(abc.ABC):

    @abc.abstractmethod
    def _call(self, query: Union[str, ChatCompletion]):
        raise NotImplemented

    @abc.abstractmethod
    def __call__(self, query: Union[str, ChatCompletion]):
        return unify.log(self._call(unify.handle_query(query)))
