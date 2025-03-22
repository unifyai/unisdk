import builtins
import traceback

import unify
from openai.types.chat import ChatCompletion


class SimulateInput:
    def __init__(self):
        self._message = "Hi, how can I help you?"
        self._true_input = None

    def _new_input(self, user_instructions):
        if user_instructions is not None:
            print(user_instructions)
        print(self._message)
        return self._message

    def __enter__(self):
        self._true_input = builtins.__dict__["input"]
        builtins.__dict__["input"] = self._new_input

    def __exit__(self, exc_type, exc_value, tb):
        builtins.__dict__["input"] = self._true_input
        self._count = 0
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            return False
        return True


def test_user_input_client():
    client = unify.Unify("user-input")
    with SimulateInput():
        response = client.generate("hello")
        assert isinstance(response, str)
        response = client.generate("hello", return_full_completion=True)
        assert isinstance(response, ChatCompletion)


if __name__ == "__main__":
    pass
