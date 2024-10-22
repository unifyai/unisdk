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

    def test_versioned(self):
        system_prompt = unify.versioned("you are an expert")
        assert system_prompt.version == 0
        assert system_prompt.value == "you are an expert"
        system_prompt.update("you are an expert mathematician")
        assert system_prompt.version == 1
        assert system_prompt.value == "you are an expert mathematician"
        assert len(system_prompt) == 2
        assert system_prompt.at_version(0).value == "you are an expert"
        assert system_prompt.value == "you are an expert mathematician"
        system_prompt.set_version(0)
        assert system_prompt.value == "you are an expert"
