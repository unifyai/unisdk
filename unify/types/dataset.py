from typing import Union
from pydantic import Extra

import unify
from .chat import Prompt
from .base import _FormattedBaseModel


class Datum(_FormattedBaseModel, extra=Extra.allow):

    def __init__(self, prompt: Union[str, Prompt] = None, **kwargs):
        """
        Create Datum instance.

        Args:
            prompt: Optional prompt passed directly.

            kwargs: All the data fields to pass.

        Returns:
            The pydantic Datum instance.
        """
        if prompt is not None:
            kwargs["prompt"] = prompt
        kwargs = {k: unify.try_cast(v, [Prompt]) for k, v in kwargs.items()}
        super().__init__(**kwargs)

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
