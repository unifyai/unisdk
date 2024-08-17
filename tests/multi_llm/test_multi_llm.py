import os
import unittest
from unify.multi_llm import MultiLLM
from unify.exceptions import UnifyError


class TestUnifyBasics(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_api_key = os.environ.get("UNIFY_KEY")

    def test_constructor(self) -> None:
        MultiLLM(api_key=self.valid_api_key, endpoints=["llama-3-8b-chat@together-ai", "gpt-4o@openai"])

    def test_add_endpoints(self):
        endpoints = ("llama-3-8b-chat@together-ai", "gpt-4o@openai")
        client = MultiLLM(api_key=self.valid_api_key, endpoints=endpoints)
        assert client.endpoints == endpoints
        assert tuple(client.clients.keys()) == endpoints
        client.add_endpoints("claude-3.5-sonnet@anthropic")
        endpoints = ("llama-3-8b-chat@together-ai", "gpt-4o@openai", "claude-3.5-sonnet@anthropic")
        assert client.endpoints == endpoints
        assert tuple(client.clients.keys()) == endpoints
        client.add_endpoints("claude-3.5-sonnet@anthropic")
        assert client.endpoints == endpoints
        assert tuple(client.clients.keys()) == endpoints
        with self.assertRaises(UnifyError):
            client.add_endpoints("claude-3.5-sonnet@anthropic", ignore_duplicates=False)

    def test_remove_endpoints(self):
        endpoints = ("llama-3-8b-chat@together-ai", "gpt-4o@openai", "claude-3.5-sonnet@anthropic")
        client = MultiLLM(api_key=self.valid_api_key, endpoints=endpoints)
        assert client.endpoints == endpoints
        assert tuple(client.clients.keys()) == endpoints
        client.remove_endpoints("claude-3.5-sonnet@anthropic")
        endpoints = ("llama-3-8b-chat@together-ai", "gpt-4o@openai")
        assert client.endpoints == endpoints
        assert tuple(client.clients.keys()) == endpoints
        client.remove_endpoints("claude-3.5-sonnet@anthropic")
        assert client.endpoints == endpoints
        assert tuple(client.clients.keys()) == endpoints
        with self.assertRaises(UnifyError):
            client.remove_endpoints("claude-3.5-sonnet@anthropic", ignore_missing=False)

    def test_generate(self):
        endpoints = ("llama-3-8b-chat@together-ai", "gpt-4o@openai", "claude-3.5-sonnet@anthropic")
        client = MultiLLM(api_key=self.valid_api_key, endpoints=endpoints)
        responses = client.generate("Hello, how it is going?")
        for endpoint, (response_endpoint, response) in zip(endpoints, responses.items()):
            assert endpoint == response_endpoint
            assert isinstance(response, str)
            assert len(response)
