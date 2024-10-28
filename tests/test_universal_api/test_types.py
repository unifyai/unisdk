import os
import unittest

import unify

dir_path = os.path.dirname(os.path.realpath(__file__))


class TestPrompt(unittest.TestCase):

    def _assert_prompt_msg(self, prompt, user_msg):
        self.assertIn("messages", prompt.__dict__)
        self.assertIsInstance(prompt.messages, list)
        self.assertGreater(len(prompt.messages), 0)
        self.assertIn("content", prompt.messages[0])
        self.assertEqual(prompt.messages[0]["content"], user_msg)

    def _assert_prompt_param(self, prompt, param_name, param_val):
        self.assertIn(param_name, prompt.__dict__)
        self.assertEqual(prompt.__dict__[param_name], param_val)

    def test_create_prompt_from_user_message(self) -> None:
        prompt = unify.Prompt("Hello")
        self._assert_prompt_msg(prompt, "Hello")

    def test_create_prompt_from_messages(self) -> None:
        prompt = unify.Prompt(messages=[{"role": "user", "content": "Hello"}])
        self._assert_prompt_msg(prompt, "Hello")

    def test_create_prompt_from_messages_n_params(self) -> None:
        prompt = unify.Prompt(
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.5,
        )
        self._assert_prompt_msg(prompt, "Hello")
        self._assert_prompt_param(prompt, "temperature", 0.5)

    def test_pass_prompts_to_client(self) -> None:
        prompt = unify.Prompt(
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.5,
        )
        client = unify.Unify(**prompt.model_dump())
        self.assertEqual(client.temperature, 0.5)
