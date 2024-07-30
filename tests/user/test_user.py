import unify
import unittest


class TestUser(unittest.TestCase):

    def test_get_credits(self) -> None:
        credits = unify.utils.get_credits()
        assert isinstance(credits, float)
