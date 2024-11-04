import pytest
from types import AsyncGeneratorType, GeneratorType

import unify
from unify import AsyncUnify, Unify
from unify.universal_api.types import Prompt


class TestUnifyBasics:

    def test_invalid_api_key_raises_authentication_error(self) -> None:
        with pytest.raises(Exception):
            client = Unify(
                api_key="invalid_api_key",
                endpoint="llama-3-8b-chat@together-ai",
            )
            client.generate(user_message="hello")

    def test_incorrect_model_name_raises_internal_server_error(self) -> None:
        with pytest.raises(Exception):
            Unify(model="wong-model-name")

    def test_generate_returns_string_when_stream_false(self) -> None:
        client = Unify(
            endpoint="llama-3-8b-chat@together-ai",
        )
        result = client.generate(user_message="hello", stream=False)
        assert isinstance(result, str)

    def test_generate_returns_generator_when_stream_true(self) -> None:
        client = Unify(
            endpoint="llama-3-8b-chat@together-ai",
        )
        result = client.generate(user_message="hello", stream=True)
        assert isinstance(result, GeneratorType)

    def test_default_params_handled_correctly(self) -> None:
        client = Unify(
            endpoint="gpt-4o@openai",
            n=2,
            return_full_completion=True,
        )
        result = client.generate(user_message="hello")
        assert len(result.choices) == 2

    def test_default_prompt_handled_correctly(self) -> None:
        client = Unify(
            endpoint="gpt-4o@openai",
            n=2,
            temperature=0.5,
        )
        assert client.default_prompt.temperature == 0.5
        assert client.default_prompt.n == 2
        prompt = Prompt(temperature=0.4)
        client.set_default_prompt(prompt)
        assert client.temperature == 0.4
        assert client.n is None

    def test_setter_chaining(self):
        client = Unify("gpt-4o@openai")
        client.set_temperature(0.5).set_n(2)
        assert client.temperature == 0.5
        assert client.n == 2

    def test_stateful(self):

        # via generate
        client = Unify("gpt-4o@openai", stateful=True)
        client.set_system_message("you are a good mathematician.")
        client.generate("What is 1 + 1?")
        client.generate("How do you know?")
        assert len(client.messages) == 5
        assert client.messages[0]["role"] == "system"
        assert client.messages[1]["role"] == "user"
        assert client.messages[2]["role"] == "assistant"
        assert client.messages[3]["role"] == "user"
        assert client.messages[4]["role"] == "assistant"

        # via append
        client = Unify("gpt-4o@openai", return_full_completion=True)
        client.set_stateful(True)
        client.set_system_message("You are an expert.")
        client.append_messages(
            [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Hello",
                        },
                    ],
                },
            ],
        )
        assert len(client.messages) == 2
        assert client.messages[0]["role"] == "system"
        assert client.messages[1]["role"] == "user"

    def test_seed(self):
        client = Unify("gpt-4@openai")

        correct = client.generate("tell me a random number between 0-10", seed=0)

        # generate arg
        num0 = client.generate("tell me a random number between 0-10", seed=0)
        num1 = client.generate("tell me a random number between 0-10", seed=0)
        assert num0 == num1 == correct

        # client attribute
        client.set_seed(0)
        num0 = client.generate("tell me a random number between 0-10")
        num1 = client.generate("tell me a random number between 0-10")
        assert num0 == num1 == correct

        # global state
        client.set_seed(None)
        unify.set_seed(0)
        num0 = client.generate("tell me a random number between 0-10")
        num1 = client.generate("tell me a random number between 0-10")
        assert num0 == num1 == correct


@pytest.mark.asyncio
class TestAsyncUnifyBasics:

    async def test_invalid_api_key_raises_authentication_error(self) -> None:
        with pytest.raises(Exception):
            async_client = AsyncUnify(
                api_key="invalid_api_key",
                endpoint="llama-3-8b-chat@together-ai",
            )
            await async_client.generate(user_message="hello")

    async def test_incorrect_model_name_raises_internal_server_error(self) -> None:
        with pytest.raises(Exception):
            AsyncUnify(model="wong-model-name")

    async def test_generate_returns_string_when_stream_false(self) -> None:
        async_client = AsyncUnify(
            endpoint="llama-3-8b-chat@together-ai",
        )
        result = await async_client.generate(user_message="hello", stream=False)
        assert isinstance(result, str)

    async def test_generate_returns_generator_when_stream_true(self) -> None:
        async_client = AsyncUnify(
            endpoint="llama-3-8b-chat@together-ai",
        )
        result = await async_client.generate(user_message="hello", stream=True)
        assert isinstance(result, AsyncGeneratorType)

    async def test_default_params_handled_correctly(self) -> None:
        async_client = AsyncUnify(
            endpoint="gpt-4o@openai",
            n=2,
            return_full_completion=True,
        )
        result = await async_client.generate(user_message="hello")
        assert len(result.choices) == 2

    async def test_default_prompt_handled_correctly(self) -> None:
        client = AsyncUnify(
            endpoint="gpt-4o@openai",
            n=2,
            temperature=0.5,
        )
        assert client.default_prompt.temperature == 0.5
        assert client.default_prompt.n == 2
        prompt = Prompt(temperature=0.4)
        client.set_default_prompt(prompt)
        assert client.temperature == 0.4
        assert client.n is None


if __name__ == "__main__":
    pass
