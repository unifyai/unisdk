import os
import unify
import unittest

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
        prompt = unify.Prompt(
            messages=[{"role": "user", "content": "Hello"}]
        )
        self._assert_prompt_msg(prompt, "Hello")

    def test_create_prompt_from_messages_n_params(self) -> None:
        prompt = unify.Prompt(
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.5
        )
        self._assert_prompt_msg(prompt, "Hello")
        self._assert_prompt_param(prompt, "temperature", 0.5)

    def test_pass_prompts_to_client(self) -> None:
        prompt = unify.Prompt(
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.5
        )
        client = unify.Unify(**prompt.model_dump())
        self.assertEqual(client.temperature, 0.5)


class TestDatum(unittest.TestCase):

    def _assert_datum_msg(self, datum, user_msg):
        self.assertIn("prompt", datum.__dict__)
        self.assertIsInstance(datum.prompt, unify.Prompt)
        self.assertIn("messages", datum.prompt.__dict__)
        self.assertIsInstance(datum.prompt.messages, list)
        self.assertGreater(len(datum.prompt.messages), 0)
        self.assertIn("content", datum.prompt.messages[0])
        self.assertEqual(datum.prompt.messages[0]["content"], user_msg)

    def _assert_datum_param(self, datum, param_name, param_val):
        fields = {**datum.model_fields, **datum.model_extra}
        self.assertIn(param_name, fields)
        self.assertEqual(fields[param_name], param_val)

    def test_create_datum_from_user_message(self) -> None:
        datum = unify.Datum("Hello")
        self._assert_datum_msg(datum, "Hello")

    def test_create_datum_from_prompt(self) -> None:
        prompt = unify.Prompt("Hello")
        datum = unify.Datum(prompt=prompt)
        self._assert_datum_msg(datum, "Hello")

    def test_create_datum_from_prompt_n_extra(self) -> None:
        prompt = unify.Prompt("Hello")
        datum = unify.Datum(prompt=prompt, ref_answer="Answer")
        self._assert_datum_msg(datum, "Hello")
        self._assert_datum_param(datum, "ref_answer", "Answer")
