import builtins
import traceback

import unify


class SimulateInput:
    def __init__(self):
        self._messages = [
            "Hi, how can I help you?",
        ]
        self._count = 0
        self._true_input = None

    def _new_input(self, user_instructions):
        if user_instructions is not None:
            print(user_instructions)
        message = self._messages[self._count]
        self._count += 1
        print(message)
        return message

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
        client.generate("hello")


if __name__ == "__main__":
    pass
