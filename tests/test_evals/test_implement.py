import os
import builtins
import traceback

import unify
import unittest


class ImplementHandler:

    def __enter__(self):
        if os.path.exists("implementations.py"):
            os.remove("implementations.py")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.exists("implementations.py"):
            os.remove("implementations.py")


# noinspection DuplicatedCode
class SimulateInput:

    def __init__(self):
        self._messages = [
            "Yes: could you please make use of the add operation via "
            "`from operator import add` instead of using the + symbol?",
            "Yes: can you also add a comment explaining what `add` does?",
            "",
        ]
        self._count = 0
        self._true_input = None

    def _new_input(self):
        message = self._messages[self._count]
        self._count += 1
        print("\n" + message)
        return message

    @property
    def num_interactions(self):
        return self._count

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


class TestZeroShotImplement(unittest.TestCase):

    @staticmethod
    @unify.implement
    def add_two_numbers(x: int, y: int):
        """
        Add two integers together.

        Args:
            x: First integer to add.
            y: Second integer to add.

        Returns:
            The sum of the two integers.
        """
        pass

    def test_implement_non_interactive(self):
        with ImplementHandler(), unify.Interactive(False):
            assert self.add_two_numbers(1, 1) == 2

    def test_implement_interactive(self):
        simulate_input = SimulateInput()
        with ImplementHandler(), unify.Interactive(True), simulate_input:
            assert self.add_two_numbers(1, 1) == 2
            assert simulate_input.num_interactions == 3
