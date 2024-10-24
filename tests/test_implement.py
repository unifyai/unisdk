import os
import time

import unify
import unittest


class ImplementHandler:

    def __enter__(self):
        if os.path.exists("implementations.py"):
            os.remove("implementations.py")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.exists("implementations.py"):
            os.remove("implementations.py")


class TestImplement(unittest.TestCase):

    def test_implement(self):

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

        with ImplementHandler():
            t0 = time.perf_counter()
            assert add_two_numbers(1, 1) == 2
            t1 = time.perf_counter()
            add_two_numbers(1, 1)
            t2 = time.perf_counter()
            assert (t2 - t1) * 10 < t1 - t0
