from pydantic import Extra
from typing import List, Literal, Optional, Union

import unify
from .base import _FormattedBaseModel


class Datum(_FormattedBaseModel, extra=Extra.allow):

    def __init__(self, prompt: Optional[str] = None, /, **kwargs):
        """
        Create Datum instance.

        Args:
            prompt: Optional positional-only prompt,
            very common to store thus special treatment.

            kwargs: All the data fields to pass.

        Returns:
            The pydantic Datum instance.
        """
        if prompt is not None:
            kwargs["prompt"] = unify.cast(prompt, unify.Prompt)
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


class Dataset(_FormattedBaseModel, extra=Extra.allow):
    prompts: List[Union[Datum, Literal["..."]]] # type: ignore

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
