import pytest
from unify import AsyncMultiUnify, MultiUnify


class TestMultiUnify:
    def test_constructor(self) -> None:
        MultiUnify(
            endpoints=["llama-3-8b-chat@together-ai", "gpt-4o@openai"],
            cache=True,
        )

    def test_add_endpoints(self):
        endpoints = ("llama-3-8b-chat@together-ai", "gpt-4o@openai")
        client = MultiUnify(endpoints=endpoints, cache=True)
        assert client.endpoints == endpoints
        assert tuple(client.clients.keys()) == endpoints
        client.add_endpoints("claude-3.7-sonnet@anthropic")
        endpoints = (
            "llama-3-8b-chat@together-ai",
            "gpt-4o@openai",
            "claude-3.7-sonnet@anthropic",
        )
        assert client.endpoints == endpoints
        assert tuple(client.clients.keys()) == endpoints
        client.add_endpoints("claude-3.7-sonnet@anthropic")
        assert client.endpoints == endpoints
        assert tuple(client.clients.keys()) == endpoints
        with pytest.raises(Exception):
            client.add_endpoints("claude-3.7-sonnet@anthropic", ignore_duplicates=False)

    def test_remove_endpoints(self):
        endpoints = (
            "llama-3-8b-chat@together-ai",
            "gpt-4o@openai",
            "claude-3.7-sonnet@anthropic",
        )
        client = MultiUnify(endpoints=endpoints, cache=True)
        assert client.endpoints == endpoints
        assert tuple(client.clients.keys()) == endpoints
        client.remove_endpoints("claude-3.7-sonnet@anthropic")
        endpoints = ("llama-3-8b-chat@together-ai", "gpt-4o@openai")
        assert client.endpoints == endpoints
        assert tuple(client.clients.keys()) == endpoints
        client.remove_endpoints("claude-3.7-sonnet@anthropic")
        assert client.endpoints == endpoints
        assert tuple(client.clients.keys()) == endpoints
        with pytest.raises(Exception):
            client.remove_endpoints("claude-3.7-sonnet@anthropic", ignore_missing=False)

    def test_generate(self):
        endpoints = (
            "gpt-4o@openai",
            "claude-3.7-sonnet@anthropic",
        )
        client = MultiUnify(endpoints=endpoints, cache=True)
        responses = client.generate("Hello, how it is going?")
        for endpoint, (response_endpoint, response) in zip(
            endpoints,
            responses.items(),
        ):
            assert endpoint == response_endpoint
            assert isinstance(response, str)
            assert len(response) > 0

    def test_multi_message_histories(self):
        endpoints = ("claude-3.7-sonnet@anthropic", "gpt-4o@openai")
        messages = {
            "claude-3.7-sonnet@anthropic": [
                {"role": "assistant", "content": "Let's talk about cats"},
            ],
            "gpt-4o@openai": [
                {"role": "assistant", "content": "Let's talk about dogs"},
            ],
        }
        animals = {"claude-3.7-sonnet@anthropic": "cat", "gpt-4o@openai": "dog"}
        client = MultiUnify(
            endpoints=endpoints,
            messages=messages,
            cache=True,
        )
        responses = client.generate("What animal did you want to talk about?")
        for endpoint, (response_endpoint, response) in zip(
            endpoints,
            responses.items(),
        ):
            assert endpoint == response_endpoint
            assert isinstance(response, str)
            assert len(response) > 0
            assert animals[endpoint] in response.lower()

    def test_setter_chaining(self):
        endpoints = (
            "llama-3-8b-chat@together-ai",
            "gpt-4o@openai",
            "claude-3.7-sonnet@anthropic",
        )
        client = MultiUnify(endpoints=endpoints, cache=True)
        client.add_endpoints(["gpt-4@openai", "gpt-4-turbo@openai"]).remove_endpoints(
            "claude-3.7-sonnet@anthropic",
        )
        assert set(client.endpoints) == {
            "llama-3-8b-chat@together-ai",
            "gpt-4o@openai",
            "gpt-4@openai",
            "gpt-4-turbo@openai",
        }


@pytest.mark.asyncio
class TestAsyncMultiUnify:
    async def test_async_generate(self):
        endpoints = (
            "gpt-4o@openai",
            "claude-3.7-sonnet@anthropic",
        )
        client = AsyncMultiUnify(endpoints=endpoints, cache=True)
        responses = await client.generate("Hello, how it is going?")
        for endpoint, (response_endpoint, response) in zip(
            endpoints,
            responses.items(),
        ):
            assert endpoint == response_endpoint
            assert isinstance(response, str)
            assert len(response) > 0


if __name__ == "__main__":
    pass
