from typing import Union, Type
from unify.types import Prompt, Datum, ChatCompletion, Score


# Upcasting

def _usr_msg_to_prompt(user_message: str) -> Prompt:
    return Prompt(user_message)


def _prompt_to_datum(prompt: Prompt) -> Datum:
    return Datum(prompt=prompt)


def _usr_msg_to_datum(user_message: str) -> Datum:
    return _prompt_to_datum(_usr_msg_to_prompt(user_message))


def _assis_msg_to_chat_completion(assistant_message: str) -> ChatCompletion:
    return ChatCompletion(assistant_message)


def _bool_to_float(boolean: bool) -> float:
    return float(boolean)


def _float_to_score(float_in: float, score_type: Type[Score]) -> Score:
    return score_type(float_in)


def _bool_to_score(boolean: bool, score_type: Type[Score]) -> Score:
    return _float_to_score(_bool_to_float(boolean), score_type)


# Downcasting

def _prompt_to_usr_msg(prompt: Prompt) -> str:
    return prompt.messages[-1]["content"]


def _datum_to_prompt(datum: Datum) -> Prompt:
    return datum.prompt


def _datum_to_usr_msg(datum: Datum) -> str:
    return _prompt_to_usr_msg(_datum_to_prompt(datum))


def _chat_completion_to_assis_msg(chat_completion: ChatCompletion) -> str:
    return chat_completion.choices[0].message.content


def _float_to_bool(float_in: float) -> bool:
    return bool(float_in)


def _score_to_float(score: Score) -> float:
    return score.score[0]


def _score_to_bool(score: Score) -> bool:
    return _float_to_bool(_score_to_float(score))


# Cast Dict

_CAST_DICT = {
    str: {
        Prompt: _usr_msg_to_prompt,
        Datum: _usr_msg_to_datum,
        ChatCompletion: _assis_msg_to_chat_completion
    },
    Prompt: {
        str: _prompt_to_usr_msg,
        Datum: _prompt_to_datum
    },
    Datum: {
        str: _datum_to_usr_msg,
        Prompt: _datum_to_prompt
    },
    ChatCompletion: {
        str: _chat_completion_to_assis_msg
    },
    bool: {
        float: _bool_to_float,
        Score: _bool_to_score
    },
    float: {
        bool: _float_to_bool,
        Score: _float_to_score
    },
    Score: {
        bool: _score_to_bool,
        float: _score_to_float
    }
}


# Public function

def cast(
        input: Union[str, bool, float, Score, Prompt, Datum, ChatCompletion],
        to_type: Type[Union[str, bool, float, Score, Prompt, Datum, ChatCompletion]],
) -> Union[str, bool, float, Score, Prompt, Datum, ChatCompletion]:
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
    if issubclass(to_type, Score):
        return _CAST_DICT[input_type][Score](input, to_type)
    return _CAST_DICT[input_type][to_type](input)
