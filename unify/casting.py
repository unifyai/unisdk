from typing import Union, Type
from unify.types import Prompt, Datum


# Upcasting

def _usr_msg_to_prompt(user_message: str) -> Prompt:
    return Prompt(user_message)


def _prompt_to_datum(prompt: Prompt) -> Datum:
    return Datum(prompt=prompt)


def _usr_msg_to_datum(user_message: str) -> Datum:
    return _prompt_to_datum(_usr_msg_to_prompt(user_message))


# Downcasting

def _prompt_to_usr_msg(prompt: Prompt) -> str:
    return prompt.messages[-1]["content"]


def _datum_to_prompt(datum: Datum) -> Prompt:
    return datum.prompt


def _datum_to_usr_msg(datum: Datum) -> str:
    return _prompt_to_usr_msg(_datum_to_prompt(datum))


# Cast Dict

_CAST_DICT = {
    str: {
        Prompt: _usr_msg_to_prompt,
        Datum: _usr_msg_to_datum
    },
    Prompt: {
        str: _prompt_to_usr_msg,
        Datum: _prompt_to_datum
    },
    Datum: {
        str: _datum_to_usr_msg,
        Prompt: _datum_to_prompt
    }
}


# Public function

def cast(
        input: Union[str, Prompt, Datum],
        to_type: Type[Union[str, Prompt, Datum]],
) -> Union[str, Prompt, Datum]:
    """
    Cast the input to the specified type.

    Args:
        input: The input to cast.

        to_type: The type to cast the input to.

    Returns:
        The input after casting to the new type.
    """
    input_type = type(input)
    if input_type is to_type:
        return input
    return _CAST_DICT[input_type][to_type](input)
