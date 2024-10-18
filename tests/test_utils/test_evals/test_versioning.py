import unify
import unittest


class TestVersioning(unittest.TestCase):

    @staticmethod
    def my_func():
        a = 1 + 2
        b = a + 3
        return b

    def test_get_code(self):
        assert (
            unify.get_code(self.my_func)
            == "    @staticmethod\n    def my_func():\n        a = 1 + 2\n        "
            "b = a + 3\n        return b\n"
        )
