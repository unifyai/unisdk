import abc
import inspect
from rich.console import Console
from pydantic import BaseModel
from pydantic import create_model
from pydantic._internal._model_construction import ModelMetaclass

import unify


class _Formatted(abc.ABC):

    def _repr(self, item) -> str:
        class_ = item.__class__
        item = class_(**self._truncate_model(item))
        console = Console()
        with console.capture() as capture:
            console.print(item)
        return capture.get().strip("\n")

    def __repr__(self) -> str:
        return self._repr(self)

    def __str__(self) -> str:
        return self._repr(self)

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
        if isinstance(dct, BaseModel):
            dct = dct.model_dump()
        if not inspect.isclass(val) or not issubclass(val, BaseModel):
            return type(dct)
        config = {k: (self._prune_pydantic(val.model_fields[k].annotation, v),
                      None) for k, v in dct.items()}
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

    def _create_pydantic_model(self, item, dct):
        if isinstance(dct, BaseModel):
            dct = dct.model_dump()
        fields = item.model_fields
        if item.model_extra is not None:
            fields = {**fields, **item.model_extra}
        config = {k: (self._prune_pydantic(self._annotation(fields[k]), v),
                      None) for k, v in dct.items()}
        model = create_model(
                item.__class__.__name__,
                **config,
                __cls_kwargs__={"arbitrary_types_allowed": True}
            )
        return model(**dct)

    def _truncate_model(self, item, cutoff=5):
        if isinstance(item, list):
            new_items = [
                self._truncate_model(it) for it in item[:cutoff]
            ]
            if len(item) > cutoff:
                new_items.append("...")
            return new_items
        if isinstance(item, BaseModel):
            item = item.model_dump()
        if isinstance(item, dict):
            return {
                key: self._truncate_model(value)
                for key, value in item.items()
            }
        return item

    def _prune(self, item):
        prune_policy = unify.key_repr(item)
        dct = self._prune_dict(item.model_dump(), prune_policy)
        return self._create_pydantic_model(item, dct)


class _FormattedBaseModel(_Formatted, BaseModel):

    def __repr__(self) -> str:
        return self._repr(self._prune(self) if unify.repr_mode() == "concise" else self)

    def __str__(self) -> str:
        return self._repr(self._prune(self) if unify.repr_mode() == "concise" else self)

    def full_repr(self):
        """
        Return the full un-pruned representation, regardless of the mode currently set.
        """
        with unify.ReprMode("verbose"):
            return self._repr(self)
