import abc
import inspect
import rich.repr
from io import StringIO
from rich.console import Console
from pydantic import BaseModel
from pydantic import create_model
from pydantic._internal._model_construction import ModelMetaclass

import unify

RICH_CONSOLE = Console(file=StringIO())


class _Formatted(abc.ABC):

    @staticmethod
    def _repr(to_print):
        # ToDO find more elegant way to do this
        global RICH_CONSOLE
        with RICH_CONSOLE.capture() as capture:
            RICH_CONSOLE.print(to_print)
        return capture.get()

    def __repr__(self) -> str:
        return self._repr(self)

    def __str__(self) -> str:
        return self._repr(self)


@rich.repr.auto
class _FormattedBaseModel(_Formatted, BaseModel):

    def _prune_dict(self, val, prune_policy):

        def keep(v, k=None, prune_pol=None):
            if v is None:
                return False
            if not prune_pol:
                return True
            if isinstance(prune_pol, dict) and \
                    "keep" not in prune_pol and "skip" not in prune_pol:
                return True
            if "keep" in prune_pol:
                if k not in prune_pol["keep"]:
                    return False
                prune_val = prune_pol["keep"][k]
                return prune_val is None or prune_val == v
            elif "skip" in prune_pol:
                if k not in prune_pol["skip"]:
                    return True
                prune_val = prune_pol["skip"][k]
                return prune_val is not None and prune_val != v
            else:
                raise Exception("expected prune_pol to contain either 'keep' or 'skip',"
                                "but neither were present: {}.".format(prune_pol))

        if not isinstance(val, dict) and not isinstance(val, list) and \
                not isinstance(val, tuple):
            return val
        elif isinstance(val, dict):
            return {
                k: self._prune_dict(
                    v, prune_policy[k] if
                    (isinstance(prune_policy, dict) and k in prune_policy) else None
                ) for k, v in val.items() if keep(v, k, prune_policy)
            }
        elif isinstance(val, list):
            return [
                self._prune_dict(
                    v, prune_policy[i] if
                    (isinstance(prune_policy, list) and i < len(prune_policy))
                    else None
                ) for i, v in enumerate(val) if keep(v, prune_pol=prune_policy)
            ]
        else:
            return (
                self._prune_dict(
                    v, prune_policy[i] if
                    (isinstance(prune_policy, tuple) and i < len(prune_policy))
                    else None
                ) for i, v in enumerate(val) if keep(v, prune_pol=prune_policy)
            )

    def _prune_pydantic(self, val, dct):
        if not inspect.isclass(val) or not issubclass(val, BaseModel):
            return val
        config = {k: (self._prune_pydantic(val.model_fields[k].annotation, v),
                      val.model_fields[k].default) for k, v in dct.items()}
        if isinstance(val, ModelMetaclass):
            name = val.__qualname__
        else:
            name = val.__class__.__name__
        return create_model(name, **config)

    @staticmethod
    def _annotation(v):
        if hasattr(v, "annotation"):
            return v.annotation
        return type(v)

    @staticmethod
    def _default(v):
        if hasattr(v, "default"):
            return v.default
        return None

    def _prune(self):
        prune_policy = unify.key_repr(self)
        dct = self._prune_dict(self.model_dump(), prune_policy)
        fields = self.model_fields
        if self.model_extra is not None:
            fields = {**fields, **self.model_extra}
        config = {k: (self._prune_pydantic(self._annotation(fields[k]), v),
                      self._default(fields[k])) for k, v in dct.items()}
        return create_model(
            self.__class__.__name__,
            **config,
            __cls_kwargs__={"arbitrary_types_allowed": True}
        )(**dct)

    def __repr__(self) -> str:
        return self._repr(self._prune() if unify.repr_mode() == "concise" else self)

    def __str__(self) -> str:
        return self._repr(self._prune() if unify.repr_mode() == "concise" else self)

    def __rich_repr__(self):
        rep = self._prune() if unify.repr_mode() == "concise" else self
        for k in rep.model_fields:
            yield k, rep.__dict__[k]
        if rep.model_extra is None:
            return
        for k, v in rep.model_extra.items():
            yield k, v

    def full_repr(self):
        """
        Return the full un-pruned representation, regardless of the mode currently set.
        """
        with unify.ReprMode("verbose"):
            return self._repr(self)
