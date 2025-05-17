import pytest
from unify import AsyncUnify, Unify


class TestStateful:
    # ──────────────────────────────── SYNC ──────────────────────────────── #
    def test_stateful_sync_non_stream(self):
        client = Unify(endpoint="gpt-4o@openai", cache=True, stateful=True)

        client.generate(user_message="hi")  # non-stream
        assert len(client.messages) == 2  # user + assistant
        assert client.messages[-1]["role"] == "assistant"
        assert isinstance(client.messages[-1]["content"], str)

    def test_stateful_sync_stream(self):
        client = Unify(endpoint="gpt-4o@openai", cache=True, stateful=True)

        chunks = list(client.generate(user_message="hello", stream=True))
        assert all([isinstance(c, str) for c in chunks])
        assert len(client.messages) == 2  # user + assistant
        assert isinstance(client.messages[-1]["content"], str)

    def test_stateless_sync_stream_clears_history(self):
        client = Unify(endpoint="gpt-4o@openai", stateful=False)

        list(client.generate(user_message="hello", stream=True))
        assert client.messages == []  # history wiped

    # ─────────────────────────────── ASYNC ──────────────────────────────── #
    @pytest.mark.asyncio
    async def test_stateful_async_non_stream(self):
        client = AsyncUnify(endpoint="gpt-4o@openai", cache=True, stateful=True)

        await client.generate(user_message="hi")  # non-stream
        assert len(client.messages) == 2  # user + assistant
        assert isinstance(client.messages[-1]["content"], str)

    @pytest.mark.asyncio
    async def test_stateful_async_stream(self):
        client = AsyncUnify(endpoint="gpt-4o@openai", cache=True, stateful=True)

        stream = await client.generate(user_message="hello", stream=True)
        assert all([isinstance(c, str) async for c in stream])
        assert len(client.messages) == 2  # user + assistant
        assert isinstance(client.messages[-1]["content"], str)
