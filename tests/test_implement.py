import unify
import unittest


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

        assert add_two_numbers(1, 1) == 2
