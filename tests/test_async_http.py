"""Tests for the shared aiohttp client used by async SDK helpers."""

from __future__ import annotations

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from unisdk.utils import async_http


def _make_response(*, status: int = 200, payload: dict | None = None):
    body = payload if payload is not None else {"status": "ok"}
    resp = AsyncMock()
    resp.status = status
    resp.headers = {"content-type": "application/json"}
    resp.text = AsyncMock(return_value=json.dumps(body))

    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=resp)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


@pytest.mark.asyncio
async def test_async_http_post_returns_json_payload() -> None:
    await async_http.close()
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.closed = False
    mock_session.request = MagicMock(
        return_value=_make_response(payload={"status": "ok", "id": 7}),
    )

    with patch.object(async_http, "_get_session", AsyncMock(return_value=mock_session)):
        result = await async_http.post(
            "http://orchestra.test/v0/integrations/tools/tool-1/run",
            headers={"Authorization": "Bearer test"},
            json={"arguments": {"query": "alice"}},
        )

    assert result == {"status": "ok", "id": 7}
    assert mock_session.request.call_args.args[0] == "POST"
    await async_http.close()


@pytest.mark.asyncio
async def test_async_http_request_raises_request_error_on_4xx() -> None:
    await async_http.close()
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.closed = False
    mock_session.request = MagicMock(
        return_value=_make_response(status=403, payload={"detail": "forbidden"}),
    )

    with patch.object(async_http, "_get_session", AsyncMock(return_value=mock_session)):
        with pytest.raises(async_http.RequestError) as exc_info:
            await async_http.post("http://orchestra.test/v0/x", json={})

    assert exc_info.value.status == 403
    await async_http.close()


@pytest.mark.asyncio
async def test_async_http_overlaps_in_flight_requests() -> None:
    """Concurrent awaits must overlap — the bug that serialized integrations."""

    await async_http.close()
    in_flight = 0
    max_in_flight = 0
    gate = asyncio.Lock()

    def _slow_cm(*_args, **_kwargs):
        body = {"status": "ok"}
        resp = AsyncMock()
        resp.status = 200
        resp.headers = {"content-type": "application/json"}
        resp.text = AsyncMock(return_value=json.dumps(body))

        cm = AsyncMock()

        async def _enter(_self=None):
            nonlocal in_flight, max_in_flight
            async with gate:
                in_flight += 1
                max_in_flight = max(max_in_flight, in_flight)
            await asyncio.sleep(0.15)
            async with gate:
                in_flight -= 1
            return resp

        cm.__aenter__ = _enter
        cm.__aexit__ = AsyncMock(return_value=False)
        return cm

    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.closed = False
    mock_session.request = MagicMock(side_effect=_slow_cm)

    with patch.object(async_http, "_get_session", AsyncMock(return_value=mock_session)):
        started = time.monotonic()
        results = await asyncio.gather(
            *(
                async_http.post(f"http://orchestra.test/v0/tools/{i}/run", json={})
                for i in range(5)
            ),
        )
        elapsed = time.monotonic() - started

    assert len(results) == 5
    assert max_in_flight >= 4
    # Serial would be ~0.75s; overlapped should finish near one sleep.
    assert elapsed < 0.45
    await async_http.close()
