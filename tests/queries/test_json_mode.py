import os
import json
import unittest

from unify.clients import Unify


class TestUnifyJsonMode(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_api_key = os.environ.get("UNIFY_KEY")

    def test_openai_json_mode(self) -> None:
        client = Unify(api_key=self.valid_api_key, endpoint="gpt-4o@openai")
        result = client.generate(
            system_prompt="You are a helpful assistant designed to output JSON.",
            user_prompt="Who won the world series in 2020?",
            response_format={"type": "json_object"},
        )
        self.assertIsInstance(result, str)
        result = json.loads(result)
        self.assertIsInstance(result, dict)

    def test_anthropic_json_mode(self) -> None:
        client = Unify(api_key=self.valid_api_key, endpoint="claude-3-opus@anthropic")
        result = client.generate(
            system_prompt="You are a helpful assistant designed to output JSON.",
            user_prompt="Who won the world series in 2020?",
        )
        self.assertIsInstance(result, str)
        result = json.loads(result)
        self.assertIsInstance(result, dict)


if __name__ == "__main__":
    unittest.main()
