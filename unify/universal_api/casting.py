from typing import List, Type, Union

from openai.types.chat import ChatCompletion
from unify.universal_api.types import Prompt

# Upcasting


def _usr_msg_to_prompt(user_message: str) -> Prompt:
    return Prompt(user_message)


def _bool_to_float(boolean: bool) -> float:
    return float(boolean)


# Downcasting


def _prompt_to_usr_msg(prompt: Prompt) -> str:
    return prompt.messages[-1]["content"]


def _chat_completion_to_assis_msg(chat_completion: ChatCompletion) -> str:
    return chat_completion.choices[0].message.content


def _float_to_bool(float_in: float) -> bool:
    return bool(float_in)


# Cast Dict

_CAST_DICT = {
    str: {Prompt: _usr_msg_to_prompt},
    Prompt: {
        str: _prompt_to_usr_msg,
    },
    ChatCompletion: {str: _chat_completion_to_assis_msg},
    bool: {
        float: _bool_to_float,
    },
    float: {
        bool: _float_to_bool,
    },
}


def _cast_from_selection(
    inp: Union[str, bool, float, Prompt, ChatCompletion],
    targets: List[Union[float, Prompt, ChatCompletion]],
) -> Union[str, bool, float, Prompt, ChatCompletion]:
    """
    Upcasts the input if possible, based on the permitted upcasting targets provided.

    Args:
        inp: The input to cast.

        targets: The set of permitted upcasting targets.

    Returns:
        The input after casting to the new type, if it was possible.
    """
    input_type = type(inp)
    assert input_type in _CAST_DICT, (
        "Cannot upcast input {} of type {}, because this type is not in the "
        "_CAST_DICT, meaning there are no functions for casting this type."
    )
    cast_fns = _CAST_DICT[input_type]
    targets = [target for target in targets if target in cast_fns]
    assert len(targets) == 1, "There must be exactly one valid casting target."
    to_type = targets[0]
    return cast_fns[to_type](inp)


# Public function


def cast(
    inp: Union[str, bool, float, Prompt, ChatCompletion],
    to_type: Union[
        Type[Union[str, bool, float, Prompt, ChatCompletion]],
        List[Type[Union[str, bool, float, Prompt, ChatCompletion]]],
    ],
) -> Union[str, bool, float, Prompt, ChatCompletion]:
    """
    Cast the input to the specified type.

    Args:
        inp: The input to cast.

        to_type: The type to cast the input to.

    Returns:
        The input after casting to the new type.
    """
    if isinstance(to_type, list):
        return _cast_from_selection(inp, to_type)
    input_type = type(inp)
    if input_type is to_type:
        return inp
    return _CAST_DICT[input_type][to_type](inp)


def try_cast(
    inp: Union[str, bool, float, Prompt, ChatCompletion],
    to_type: Union[
        Type[Union[str, bool, float, Prompt, ChatCompletion]],
        List[Type[Union[str, bool, float, Prompt, ChatCompletion]]],
    ],
) -> Union[str, bool, float, Prompt, ChatCompletion]:
    # noinspection PyBroadException
    try:
        return cast(inp, to_type)
    except:
        return inp
