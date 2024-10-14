import unittest

import unify


class TestCredits(unittest.TestCase):
    def test_get_credits(self) -> None:
        creds = unify.get_credits()
        assert isinstance(creds, float)
