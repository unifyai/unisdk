"""Tests for AsyncAdminClient (unify.async_admin).

Unit-level tests using mocked aiohttp responses. No real Orchestra server
required.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from unify.async_admin import AdminRequestError, AsyncAdminClient


def _make_response(*, status: int = 200, json_data: dict | None = None):
    """Build a mock aiohttp response usable as an async context manager."""
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=json_data or {})
    resp.text = AsyncMock(return_value=str(json_data or ""))

    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=resp)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


def _patch_session(client: AsyncAdminClient, side_effect):
    """Patch the client's session.request to return controlled responses."""
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.closed = False
    mock_session.request = MagicMock(side_effect=side_effect)
    client._session = mock_session
    client._session_loop = asyncio.get_running_loop()
    return mock_session


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------


class TestGetAssistantSpend:
    @pytest.mark.asyncio
    async def test_returns_parsed_json(self):
        client = AsyncAdminClient(api_key="test-key")
        data = {"cumulative_spend": 5.0, "limit": 100.0, "credit_balance": 50.0}
        _patch_session(client, lambda *a, **kw: _make_response(json_data=data))

        result = await client.get_assistant_spend(agent_id=123, month="2026-03")

        assert result == data

    @pytest.mark.asyncio
    async def test_correct_url(self):
        client = AsyncAdminClient(api_key="test-key", base_url="http://test/v0")
        data = {"cumulative_spend": 0.0}
        mock_session = _patch_session(
            client,
            lambda *a, **kw: _make_response(json_data=data),
        )

        await client.get_assistant_spend(agent_id=42, month="2026-01")

        call_args = mock_session.request.call_args
        assert call_args[0] == ("GET", "http://test/v0/admin/assistant/42/spend")
        assert call_args[1]["params"] == {"month": "2026-01"}


class TestGetUserSpend:
    @pytest.mark.asyncio
    async def test_returns_parsed_json(self):
        client = AsyncAdminClient(api_key="test-key")
        data = {"cumulative_spend": 10.0, "limit": None}
        _patch_session(client, lambda *a, **kw: _make_response(json_data=data))

        result = await client.get_user_spend(user_id="user_1", month="2026-03")

        assert result == data


class TestGetMemberSpend:
    @pytest.mark.asyncio
    async def test_returns_parsed_json(self):
        client = AsyncAdminClient(api_key="test-key")
        data = {"cumulative_spend": 20.0, "limit": 50.0}
        _patch_session(client, lambda *a, **kw: _make_response(json_data=data))

        result = await client.get_member_spend(
            user_id="user_1",
            org_id=789,
            month="2026-03",
        )

        assert result == data

    @pytest.mark.asyncio
    async def test_correct_url(self):
        client = AsyncAdminClient(api_key="test-key", base_url="http://test/v0")
        data = {"cumulative_spend": 0.0}
        mock_session = _patch_session(
            client,
            lambda *a, **kw: _make_response(json_data=data),
        )

        await client.get_member_spend(user_id="u1", org_id=5, month="2026-02")

        call_args = mock_session.request.call_args
        assert call_args[0] == (
            "GET",
            "http://test/v0/admin/organization/5/members/u1/spend",
        )


class TestGetOrgSpend:
    @pytest.mark.asyncio
    async def test_returns_parsed_json(self):
        client = AsyncAdminClient(api_key="test-key")
        data = {"cumulative_spend": 100.0, "limit": 500.0}
        _patch_session(client, lambda *a, **kw: _make_response(json_data=data))

        result = await client.get_org_spend(org_id=789, month="2026-03")

        assert result == data


class TestNotifyLimitReached:
    @pytest.mark.asyncio
    async def test_sends_post(self):
        client = AsyncAdminClient(api_key="test-key", base_url="http://test/v0")
        resp_data = {"notified": True, "reason": None, "recipient_count": 1}
        mock_session = _patch_session(
            client,
            lambda *a, **kw: _make_response(json_data=resp_data),
        )

        payload = {
            "limit_type": "assistant",
            "entity_id": "123",
            "limit_value": 100.0,
            "current_spend": 105.0,
            "month": "2026-03",
        }
        result = await client.notify_limit_reached(payload)

        assert result["notified"] is True
        call_args = mock_session.request.call_args
        assert call_args[0] == ("POST", "http://test/v0/admin/spending-limit-reached")
        assert call_args[1]["json"] == payload


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_404_raises_admin_request_error(self):
        client = AsyncAdminClient(api_key="test-key")
        _patch_session(
            client,
            lambda *a, **kw: _make_response(
                status=404,
                json_data={"detail": "Not found"},
            ),
        )

        with pytest.raises(AdminRequestError) as exc_info:
            await client.get_assistant_spend(agent_id=999, month="2026-03")

        assert exc_info.value.status == 404

    @pytest.mark.asyncio
    async def test_422_raises_admin_request_error(self):
        client = AsyncAdminClient(api_key="test-key")
        _patch_session(
            client,
            lambda *a, **kw: _make_response(
                status=422,
                json_data={"detail": "Validation error"},
            ),
        )

        with pytest.raises(AdminRequestError) as exc_info:
            await client.get_user_spend(user_id="bad", month="invalid")

        assert exc_info.value.status == 422


# ---------------------------------------------------------------------------
# Retry behavior
# ---------------------------------------------------------------------------


class TestRetryBehavior:
    @pytest.mark.asyncio
    async def test_retries_on_502_then_succeeds(self):
        """A 502 followed by a 200 should succeed after one retry."""
        client = AsyncAdminClient(
            api_key="test-key",
            backoff_factor=0.01,
        )
        data = {"cumulative_spend": 5.0}
        responses = [
            _make_response(status=502, json_data={"error": "bad gateway"}),
            _make_response(status=200, json_data=data),
        ]
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            r = responses[min(call_count, len(responses) - 1)]
            call_count += 1
            return r

        _patch_session(client, side_effect)

        result = await client.get_assistant_spend(agent_id=1, month="2026-03")

        assert result == data
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retries_on_connect_error(self):
        """Connection errors should be retried up to retry_connect times."""
        client = AsyncAdminClient(
            api_key="test-key",
            backoff_factor=0.01,
            retry_connect=2,
            retry_total=3,
        )
        data = {"cumulative_spend": 5.0}
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise aiohttp.ClientConnectionError("Connection refused")
            return _make_response(status=200, json_data=data)

        _patch_session(client, side_effect)

        result = await client.get_assistant_spend(agent_id=1, month="2026-03")

        assert result == data
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_exhausted_retries_raises(self):
        """When all retries are exhausted on connect errors, the error propagates."""
        client = AsyncAdminClient(
            api_key="test-key",
            backoff_factor=0.01,
            retry_connect=1,
            retry_total=1,
        )

        def side_effect(*args, **kwargs):
            raise aiohttp.ClientConnectionError("Connection refused")

        _patch_session(client, side_effect)

        with pytest.raises(aiohttp.ClientConnectionError):
            await client.get_assistant_spend(agent_id=1, month="2026-03")

    @pytest.mark.asyncio
    async def test_no_retry_on_4xx(self):
        """4xx errors should NOT be retried."""
        client = AsyncAdminClient(api_key="test-key", backoff_factor=0.01)
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return _make_response(status=404, json_data={"detail": "Not found"})

        _patch_session(client, side_effect)

        with pytest.raises(AdminRequestError):
            await client.get_assistant_spend(agent_id=999, month="2026-03")

        assert call_count == 1


# ---------------------------------------------------------------------------
# Connection reuse
# ---------------------------------------------------------------------------


class TestConnectionReuse:
    @pytest.mark.asyncio
    async def test_shared_session_across_calls(self):
        """Multiple calls should reuse the same aiohttp session."""
        client = AsyncAdminClient(api_key="test-key")
        data = {"cumulative_spend": 0.0}
        _patch_session(client, lambda *a, **kw: _make_response(json_data=data))

        session_before = client._session
        await client.get_assistant_spend(agent_id=1, month="2026-03")
        await client.get_user_spend(user_id="u1", month="2026-03")
        session_after = client._session

        assert session_before is session_after

    @pytest.mark.asyncio
    async def test_recreates_session_when_closed(self):
        """If the session is closed, a new one is created."""
        client = AsyncAdminClient(api_key="test-key")

        session1 = client._get_session()
        await session1.close()

        session2 = client._get_session()
        assert session1 is not session2
        assert not session2.closed

        await session2.close()

    @pytest.mark.asyncio
    async def test_closed_property(self):
        client = AsyncAdminClient(api_key="test-key")
        assert client.closed is True  # no session yet

        session = client._get_session()
        assert client.closed is False

        await session.close()
        assert client.closed is True


# ---------------------------------------------------------------------------
# Auth headers
# ---------------------------------------------------------------------------


class TestAuthHeaders:
    @pytest.mark.asyncio
    async def test_bearer_token_in_headers(self):
        client = AsyncAdminClient(api_key="my-secret-key")
        session = client._get_session()

        assert session.headers["Authorization"] == "Bearer my-secret-key"

        await session.close()
