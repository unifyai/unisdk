from pydantic import Extra
from typing import Optional, Union

import unify
from .chat import Prompt
from .base import _FormattedBaseModel


class Datum(_FormattedBaseModel, extra=Extra.allow):
    prompt: Prompt

    def __init__(self, prompt: Optional[Union[str, Prompt]], **kwargs):
        """
        Create Datum instance.

        Args:
            prompt: The prompt, either as a user message or as the full prompt.

            kwargs: Optional extra fields passed.

        Returns:
            The pydantic Datum instance.
        """
        if isinstance(prompt, str):
            prompt = Prompt(prompt)
        super().__init__(prompt=prompt, **kwargs)

    def __add__(self, other):
        if other == 0:
            return self
        return (unify.Dataset(self) +
                (other if isinstance(other, unify.Dataset) else unify.Dataset(other)))

    def __sub__(self, other):
        return unify.Dataset(self) -\
               (other if isinstance(other, unify.Dataset) else unify.Dataset(other))

    def __radd__(self, other):
        if other == 0:
            return self
        return ((other if isinstance(other, unify.Dataset) else unify.Dataset(other)) +
                unify.Dataset(self))

    def __rsub__(self, other):
        return (other if isinstance(other, unify.Dataset) else unify.Dataset(other)) -\
               unify.Dataset(self)

    def __hash__(self):
        return hash(str(self))
