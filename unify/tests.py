import os
import unittest
from types import AsyncGeneratorType, GeneratorType
from unittest.mock import MagicMock, patch

from unify.clients import AsyncUnify, Unify
from unify.exceptions import AuthenticationError, UnifyError


class TestUnify(unittest.TestCase):
    def setUp(self) -> None:
        # Set up a valid API key for testing
        self.valid_api_key = os.environ.get("UNIFY_KEY")

    def test_invalid_api_key_raises_authentication_error(self) -> None:
        # Instantiate Unify with an invalid API key
        with self.assertRaises(AuthenticationError):
            unify = Unify(
                api_key="invalid_api_key",
                endpoint="llama-2-7b-chat@anyscale",
            )
            unify.generate(user_prompt="hello")

    @patch("os.environ.get", return_value=None)
    def test_missing_api_key_raises_key_error(self, mock_get: MagicMock) -> None:
        # Initializing Unify without providing API key should raise KeyError
        with self.assertRaises(KeyError):
            Unify(endpoint="llama-2-7b-chat@anyscale")

    def test_incorrect_model_name_raises_internal_server_error(self) -> None:
        # Provide incorrect model name
        with self.assertRaises(UnifyError):
            Unify(api_key=self.valid_api_key, model="llama-chat")

    def test_generate_returns_string_when_stream_false(self) -> None:
        # Instantiate Unify with a valid API key
        unify = Unify(api_key=self.valid_api_key, endpoint="llama-2-7b-chat@anyscale")
        # Call generate with stream=False
        result = unify.generate(user_prompt="hello", stream=False)
        # Assert that the result is a string
        self.assertIsInstance(result, str)

    def test_generate_returns_generator_when_stream_true(self) -> None:
        # Instantiate Unify with a valid API key
        unify = Unify(api_key=self.valid_api_key, endpoint="llama-2-7b-chat@anyscale")
        # Call generate with stream=True
        result = unify.generate(user_prompt="hello", stream=True)
        # Assert that the result is a generator
        self.assertIsInstance(result, GeneratorType)


class TestAsyncUnify(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        # Set up a valid API key for testing
        self.valid_api_key = os.environ.get("UNIFY_KEY")

    async def test_invalid_api_key_raises_authentication_error(self) -> None:
        # Instantiate AsyncUnify with an invalid API key
        with self.assertRaises(AuthenticationError):
            async_unify = AsyncUnify(
                api_key="invalid_api_key",
                endpoint="llama-2-7b-chat@anyscale",
            )
            await async_unify.generate(user_prompt="hello")

    @patch("os.environ.get", return_value=None)
    async def test_missing_api_key_raises_key_error(self, mock_get: MagicMock) -> None:
        # Initializing AsyncUnify without providing
        # API key should raise KeyError
        with self.assertRaises(KeyError):
            async_unify = AsyncUnify()
            await async_unify.generate(user_prompt="hello")

    async def test_incorrect_model_name_raises_internal_server_error(self) -> None:
        # Provide incorrect model name
        with self.assertRaises(UnifyError):
            AsyncUnify(api_key=self.valid_api_key, model="llama-chat")

    async def test_generate_returns_string_when_stream_false(self) -> None:
        # Instantiate AsyncUnify with a valid API key
        async_unify = AsyncUnify(
            api_key=self.valid_api_key,
            endpoint="llama-2-7b-chat@anyscale",
        )
        # Call generate with stream=False
        result = await async_unify.generate(user_prompt="hello", stream=False)
        # Assert that the result is a string
        self.assertIsInstance(result, str)

    async def test_generate_returns_generator_when_stream_true(self) -> None:
        # Instantiate AsyncUnify with a valid API key
        async_unify = AsyncUnify(
            api_key=self.valid_api_key,
            endpoint="llama-2-7b-chat@anyscale",
        )
        # Call generate with stream=True
        result = await async_unify.generate(user_prompt="hello", stream=True)
        # Assert that the result is a generator
        self.assertIsInstance(result, AsyncGeneratorType)


if __name__ == "__main__":
    unittest.main()
