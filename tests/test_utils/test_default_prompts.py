import unify
import unittest


class TestDefaultPrompts(unittest.TestCase):

    def test_default_prompt(self):
        name = "TestDefaultPrompt"
        default_prompt = {"temperature": 0.41}
        unify.utils.default_prompts.create_default_prompt(name, default_prompt)

        list_defaults = unify.utils.default_prompts.list_default_prompts()
        self.assertIn(name, list_defaults)
        get_prompt = unify.utils.default_prompts.get_default_prompt(name)
        self.assertEqual(get_prompt["prompt"]["temperature"], 0.41)

        unify.utils.default_prompts.rename_default_prompt(name, "NewDefaultPrompt")
        list_defaults = unify.utils.default_prompts.list_default_prompts()
        self.assertNotIn(name, list_defaults)
        self.assertIn("NewDefaultPrompt", list_defaults)

    def tearDown(self):
        try:
            unify.utils.default_prompts.delete_default_prompt("TestDefaultPrompt")
        except:
            pass
        try:
            unify.utils.default_prompts.delete_default_prompt("NewDefaultPrompt")
        except:
            pass
