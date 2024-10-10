import os
import unittest
from types import AsyncGeneratorType, GeneratorType
from unittest.mock import MagicMock, patch

from unify.types import Prompt
from unify import AsyncUnify, Unify


class TestChatBasics(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_api_key = os.environ.get("UNIFY_KEY")

    # Basic #
    # ------#

    def test_invalid_api_key_raises_authentication_error(self) -> None:
        with self.assertRaises(Exception):
            client = Unify(
                api_key="invalid_api_key",
                endpoint="llama-3-8b-chat@together-ai",
            )
            client.generate(user_message="hello")

    @patch("os.environ.get", return_value=None)
    def test_missing_api_key_raises_key_error(self, mock_get: MagicMock) -> None:
        with self.assertRaises(KeyError):
            Unify(endpoint="llama-3-8b-chat@together-ai")

    def test_incorrect_model_name_raises_internal_server_error(self) -> None:
        with self.assertRaises(Exception):
            Unify(api_key=self.valid_api_key, model="wong-model-name")

    def test_generate_returns_string_when_stream_false(self) -> None:
        client = Unify(
            api_key=self.valid_api_key, endpoint="llama-3-8b-chat@together-ai"
        )
        result = client.generate(user_message="hello", stream=False)
        self.assertIsInstance(result, str)

    def test_generate_returns_generator_when_stream_true(self) -> None:
        client = Unify(
            api_key=self.valid_api_key, endpoint="llama-3-8b-chat@together-ai"
        )
        result = client.generate(user_message="hello", stream=True)
        self.assertIsInstance(result, GeneratorType)

    def test_default_params_handled_correctly(self) -> None:
        client = Unify(
            api_key=self.valid_api_key,
            endpoint="gpt-4o@openai",
            n=2,
            return_full_completion=True,
        )
        result = client.generate(user_message="hello")
        self.assertEqual(len(result.choices), 2)

    def test_default_prompt_handled_correctly(self) -> None:
        client = Unify(
            api_key=self.valid_api_key, endpoint="gpt-4o@openai", n=2, temperature=0.5
        )
        self.assertEqual(client.default_prompt.temperature, 0.5)
        self.assertEqual(client.default_prompt.n, 2)
        prompt = Prompt(temperature=0.4)
        client.set_default_prompt(prompt)
        self.assertEqual(client.temperature, 0.4)
        self.assertIs(client.n, None)

    def test_setter_chaining(self):
        client = Unify("gpt-4o@openai")
        client.set_temperature(0.5).set_n(2)
        assert client.temperature == 0.5
        assert client.n == 2


class TestAsyncUnifyBasics(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.valid_api_key = os.environ.get("UNIFY_KEY")

    async def test_invalid_api_key_raises_authentication_error(self) -> None:
        with self.assertRaises(Exception):
            async_client = AsyncUnify(
                api_key="invalid_api_key",
                endpoint="llama-3-8b-chat@together-ai",
            )
            await async_client.generate(user_message="hello")

    @patch("os.environ.get", return_value=None)
    async def test_missing_api_key_raises_key_error(self, mock_get: MagicMock) -> None:
        with self.assertRaises(KeyError):
            async_client = AsyncUnify()
            await async_client.generate(user_message="hello")

    async def test_incorrect_model_name_raises_internal_server_error(self) -> None:
        with self.assertRaises(Exception):
            AsyncUnify(api_key=self.valid_api_key, model="wong-model-name")

    async def test_generate_returns_string_when_stream_false(self) -> None:
        async_client = AsyncUnify(
            api_key=self.valid_api_key,
            endpoint="llama-3-8b-chat@together-ai",
        )
        result = await async_client.generate(user_message="hello", stream=False)
        self.assertIsInstance(result, str)

    async def test_generate_returns_generator_when_stream_true(self) -> None:
        async_client = AsyncUnify(
            api_key=self.valid_api_key,
            endpoint="llama-3-8b-chat@together-ai",
        )
        result = await async_client.generate(user_message="hello", stream=True)
        self.assertIsInstance(result, AsyncGeneratorType)

    async def test_default_params_handled_correctly(self) -> None:
        async_client = AsyncUnify(
            api_key=self.valid_api_key,
            endpoint="gpt-4o@openai",
            n=2,
            return_full_completion=True,
        )
        result = await async_client.generate(user_message="hello")
        self.assertEqual(len(result.choices), 2)

    async def test_default_prompt_handled_correctly(self) -> None:
        client = AsyncUnify(
            api_key=self.valid_api_key, endpoint="gpt-4o@openai", n=2, temperature=0.5
        )
        self.assertEqual(client.default_prompt.temperature, 0.5)
        self.assertEqual(client.default_prompt.n, 2)
        prompt = Prompt(temperature=0.4)
        client.set_default_prompt(prompt)
        self.assertEqual(client.temperature, 0.4)
        self.assertIs(client.n, None)


if __name__ == "__main__":
    unittest.main()
