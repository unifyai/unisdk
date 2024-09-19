import copy
from typing import Union, List, Dict, Type
from unify.types import _FormattedBaseModel, ChatCompletion, Choice,\
    ChatCompletionMessage

_REPR_MODE = None
_KEYS_TO_SKIP: Dict[Type, Dict] = dict()
_KEYS_TO_KEEP: Dict[Type, Dict] = dict()
_KEYS_TO_KEEP_MODES: Dict[str, Dict[Type, Dict]] = {
    "concise": {
        ChatCompletion: {
            "choices": None
        }
    },
    "verbose": {}
}
_KEYS_TO_SKIP_MODES: Dict[str, Dict[Type, Dict]] = {
    "concise": {
        Choice: {
            "finish_reason": "stop",
            "index": 0
        },
        ChatCompletionMessage: {
            "role": "assistant"
        },
        "verbose": {}
    }
}


def repr_mode() -> str:
    """
    Gets the global representation mode as currently set. This is used when representing
    the various unify types on screen. Can be either "verbose" or "concise".
    """
    global _REPR_MODE
    # noinspection PyProtectedMember
    return _REPR_MODE._val if _REPR_MODE is not None else "verbose"


def key_repr(instance: _FormattedBaseModel) -> Union[Dict, List]:
    """
    Get the key representation for the instance passed, either as the keys to keep or
    the keys to remove.

    Args:
        instance: The instance for which we want to retrieve the key repr policy.

    Returns:
        Dict containing the policy, with a base key of "skip" or "keep", followed by
        the nested structure of the elements to either remove or keep.
    """
    ret = dict()
    fields = instance.model_fields
    if instance.model_extra is not None:
        fields = {**fields, **instance.model_extra}
    for key, field in fields.items():
        annotation = field.annotation
        if annotation in _KEYS_TO_SKIP or annotation in _KEYS_TO_KEEP:
            ret[key] = key_repr(getattr(instance, key))
    ins_type = type(instance)
    to_skip = ins_type in _KEYS_TO_SKIP
    to_keep = ins_type in _KEYS_TO_KEEP
    assert not (to_skip and to_keep),\
        "Cannot have specification for keys to skip AND to keep," \
        "please only set one of these."
    if to_skip:
        return {**ret, **{"skip": _KEYS_TO_SKIP[ins_type]}}
    elif to_keep:
        return {**ret, **{"keep": _KEYS_TO_KEEP[ins_type]}}
    return ret


def keys_to_skip() -> Dict[Type, Dict]:
    """
    Return the currently set keys to skip, which is a dict with types as keys and the
    nested structure to skip as values.
    """
    global _KEYS_TO_SKIP
    return copy.deepcopy(_KEYS_TO_SKIP)


def set_keys_to_skip(skip_keys: Union[Dict[Type, Dict], str]) -> None:
    """
    Set the keys to be skipped during representation, which is a dict with types as keys
    and the nested structure to skip as values.

    Args:
        skip_keys: The types as keywords arguments and dictionary representing the
        structure of the keys to skip for that type as values.
    """
    global _KEYS_TO_SKIP
    if isinstance(skip_keys, str):
        global _KEYS_TO_SKIP_MODES
        _KEYS_TO_SKIP = _KEYS_TO_SKIP_MODES[skip_keys]
        return
    _KEYS_TO_SKIP = skip_keys


def keys_to_keep() -> Dict[Type, Dict]:
    """
    Return the currently set keys to keep, which is a dict with types as keys and the
    nested structure to keep as values.
    """
    global _KEYS_TO_KEEP
    return copy.deepcopy(_KEYS_TO_KEEP)


def set_keys_to_keep(keep_keys: Union[Dict[Type, Dict], str]) -> None:
    """
    Set the keys to be kept during representation, which is a dict with types as keys
    and the nested structure to keep as values.

    Args:
        keep_keys: The types as keywords arguments and dictionary representing the
        structure of the keys to keep for that type as values.
    """
    global _KEYS_TO_KEEP
    if isinstance(keep_keys, str):
        global _KEYS_TO_KEEP_MODES
        _KEYS_TO_KEEP = _KEYS_TO_KEEP_MODES[keep_keys]
        return
    _KEYS_TO_KEEP = keep_keys


def set_repr_mode(mode: str) -> None:
    """
    Sets the global representation mode, to be used when representing the various unify
    types on screen. Can be either "verbose" or "concise".

    Args:
        mode: The value to set the mode to, either "verbose" or "concise".
    """
    global _REPR_MODE, _KEYS_TO_SKIP
    _REPR_MODE = ReprMode(mode)
    set_keys_to_skip(mode)
    set_keys_to_keep(mode)


class ReprMode(str):

    def __init__(self, val: str):
        """
        Set a representation mode for a specific context in the code, by using the
        `with` an instantiation of this class.

        Args:
            val: The value of the string, must be either "verbose" or "concise".
        """
        self._check_str(val)
        # noinspection PyProtectedMember

        self._prev_val = "verbose" if _REPR_MODE is None else repr_mode()
        self._val = val

    @staticmethod
    def _check_str(val: str):
        assert val in ("verbose", "concise"),\
            "Expected value to be either 'verbose' or 'concise', " \
            "but found {}".format(val)

    def __enter__(self) -> None:
        set_repr_mode(self._val)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._val = self._prev_val
        self._prev_val = None
        set_repr_mode(self._val)

    def __repr__(self):
        return str(self._val)

    def __str__(self):
        return str(self._val)


class KeepKeys:

    def __init__(self, keep_keys: Union[Dict[Type, Dict], str]):
        """
        Set a the keys to keep for a specific context in the code, by using the
        `with` an instantiation of this class.

        Args:
            keep_keys: The types as keywords arguments and dictionary representing the
            structure of the keys to keep for that type as values.
        """
        self._prev_val = keys_to_keep()
        self._val = keep_keys

    @staticmethod
    def _check_str(val: str):
        assert val in ("verbose", "concise"),\
            "Expected value to be either 'verbose' or 'concise', " \
            "but found {}".format(val)

    def __enter__(self) -> None:
        set_keys_to_keep(self._val)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._val = self._prev_val
        self._prev_val = None
        set_keys_to_keep(self._val)

    def __repr__(self):
        return str(self._val)

    def __str__(self):
        return str(self._val)


class SkipKeys:

    def __init__(self, skip_keys: Union[Dict[Type, Dict], str]):
        """
        Set a the keys to skip for a specific context in the code, by using the
        `with` an instantiation of this class.

        Args:
            skip_keys: The types as keywords arguments and dictionary representing the
            structure of the keys to skip for that type as values.
        """
        self._prev_val = keys_to_keep()
        self._val = skip_keys

    @staticmethod
    def _check_str(val: str):
        assert val in ("verbose", "concise"), \
            "Expected value to be either 'verbose' or 'concise', " \
            "but found {}".format(val)

    def __enter__(self) -> None:
        set_keys_to_skip(self._val)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._val = self._prev_val
        self._prev_val = None
        set_keys_to_skip(self._val)

    def __repr__(self):
        return str(self._val)

    def __str__(self):
        return str(self._val)


# noinspection PyRedeclaration
_REPR_MODE = ReprMode("verbose")
