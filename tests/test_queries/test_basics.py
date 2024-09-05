import os
import unittest
from types import AsyncGeneratorType, GeneratorType
from unittest.mock import MagicMock, patch

from unify import AsyncUnify, Unify
from unify.exceptions import AuthenticationError, UnifyError


class TestUnifyBasics(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_api_key = os.environ.get("UNIFY_KEY")

    # Basic #
    # ------#

    def test_invalid_api_key_raises_authentication_error(self) -> None:
        with self.assertRaises(AuthenticationError):
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
        with self.assertRaises(UnifyError):
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


class TestAsyncUnifyBasics(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.valid_api_key = os.environ.get("UNIFY_KEY")

    async def test_invalid_api_key_raises_authentication_error(self) -> None:
        with self.assertRaises(AuthenticationError):
            async_unify = AsyncUnify(
                api_key="invalid_api_key",
                endpoint="llama-3-8b-chat@together-ai",
            )
            await async_unify.generate(user_message="hello")

    @patch("os.environ.get", return_value=None)
    async def test_missing_api_key_raises_key_error(self, mock_get: MagicMock) -> None:
        with self.assertRaises(KeyError):
            async_unify = AsyncUnify()
            await async_unify.generate(user_message="hello")

    async def test_incorrect_model_name_raises_internal_server_error(self) -> None:
        with self.assertRaises(UnifyError):
            AsyncUnify(api_key=self.valid_api_key, model="wong-model-name")

    async def test_generate_returns_string_when_stream_false(self) -> None:
        async_unify = AsyncUnify(
            api_key=self.valid_api_key,
            endpoint="llama-3-8b-chat@together-ai",
        )
        result = await async_unify.generate(user_message="hello", stream=False)
        self.assertIsInstance(result, str)

    async def test_generate_returns_generator_when_stream_true(self) -> None:
        async_unify = AsyncUnify(
            api_key=self.valid_api_key,
            endpoint="llama-3-8b-chat@together-ai",
        )
        result = await async_unify.generate(user_message="hello", stream=True)
        self.assertIsInstance(result, AsyncGeneratorType)


if __name__ == "__main__":
    unittest.main()
