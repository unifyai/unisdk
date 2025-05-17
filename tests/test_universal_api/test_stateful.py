# tests/test_stateful_matrix.py
import pytest
from unify import AsyncUnify, Unify

# --------------------------------------------------------------------------- #
#  HELPER STUBS                                                               #
# --------------------------------------------------------------------------- #


def _stub_client(self):  # replaces _get_client so no HTTP is attempted
    return None


# ---------- synchronous stubs ---------------------------------------------- #
def _stub_sync_non_stream(self, *_, **__):
    return "stub-sync-response"


def _stub_sync_stream(self, *_, **__):
    return (chunk for chunk in ("chunk-A", "chunk-B"))


# ---------- asynchronous stubs --------------------------------------------- #
async def _stub_async_non_stream(self, *_, **__):
    return "stub-async-response"


async def _stub_async_stream(self, *_, **__):
    async def _gen():
        for chunk in ("chunk-1", "chunk-2"):
            yield chunk

    return _gen()


# --------------------------------------------------------------------------- #
#  TEST-MATRIX                                                                #
# --------------------------------------------------------------------------- #
class TestStatefulMatrix:
    # ──────────────────────────────── SYNC ──────────────────────────────── #
    def test_stateful_sync_non_stream(self, monkeypatch):
        monkeypatch.setattr(Unify, "_get_client", _stub_client)
        monkeypatch.setattr(Unify, "_generate", _stub_sync_non_stream)
        client = Unify(endpoint="gpt-4o@openai", stateful=True)

        client.generate(user_message="hi")  # non-stream
        assert len(client.messages) == 2  # user + assistant
        assert client.messages[-1]["role"] == "assistant"
        assert client.messages[-1]["content"] == "stub-sync-response"

    def test_stateful_sync_stream(self, monkeypatch):
        monkeypatch.setattr(Unify, "_get_client", _stub_client)
        monkeypatch.setattr(Unify, "_generate", _stub_sync_stream)
        client = Unify(endpoint="gpt-4o@openai", stateful=True)

        chunks = list(client.generate(user_message="hello", stream=True))
        assert chunks == ["chunk-A", "chunk-B"]  # generator intact
        assert len(client.messages) == 2  # user + assistant
        assert client.messages[-1]["content"] == "chunk-Achunk-B"

    def test_stateless_sync_stream_clears_history(self, monkeypatch):
        monkeypatch.setattr(Unify, "_get_client", _stub_client)
        monkeypatch.setattr(Unify, "_generate", _stub_sync_stream)
        client = Unify(endpoint="gpt-4o@openai", stateful=False)

        list(client.generate(user_message="hello", stream=True))
        assert client.messages == []  # history wiped

    # ─────────────────────────────── ASYNC ──────────────────────────────── #
    @pytest.mark.asyncio
    async def test_stateful_async_non_stream(self, monkeypatch):
        monkeypatch.setattr(AsyncUnify, "_get_client", _stub_client)
        monkeypatch.setattr(AsyncUnify, "_generate", _stub_async_non_stream)
        client = AsyncUnify(endpoint="gpt-4o@openai", stateful=True)

        await client.generate(user_message="hi")  # non-stream
        assert len(client.messages) == 2  # user + assistant
        assert client.messages[-1]["content"] == "stub-async-response"

    @pytest.mark.asyncio
    async def test_stateful_async_stream(self, monkeypatch):
        monkeypatch.setattr(AsyncUnify, "_get_client", _stub_client)
        monkeypatch.setattr(AsyncUnify, "_generate", _stub_async_stream)
        client = AsyncUnify(endpoint="gpt-4o@openai", stateful=True)

        stream = await client.generate(user_message="hello", stream=True)
        chunks = [c async for c in stream]
        assert chunks == ["chunk-1", "chunk-2"]
        assert len(client.messages) == 2  # user + assistant
        assert client.messages[-1]["content"] == "chunk-1chunk-2"
