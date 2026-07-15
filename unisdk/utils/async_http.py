"""Async HTTP utilities for the Unify SDK.

Mirrors the reliability characteristics of ``unisdk.utils.http`` (shared
``aiohttp`` session, connection pooling, retry/backoff on 5xx and connect/read
errors) so async call sites can overlap IO without blocking the event loop.

File-trace / OTel helpers are reused from the sync HTTP module so async and
sync traffic leave the same operator-visible audit trail under
``UNISDK_LOG_DIR``.
"""

from __future__ import annotations

import asyncio
import json as json_lib
import logging
import os
import time
from contextlib import nullcontext
from typing import Any, Dict, Optional, Set

import aiohttp

from unisdk.utils import http as sync_http

_logger = logging.getLogger("unisdk.async_http")

_RETRYABLE_STATUSES: Set[int] = {500, 502, 503, 504}

_DEFAULT_RETRY_TOTAL = 5
_DEFAULT_RETRY_CONNECT = 3
_DEFAULT_RETRY_READ = 2
_DEFAULT_BACKOFF_FACTOR = 0.1
# Integration tool runs routinely take multi-second provider round-trips.
_DEFAULT_TIMEOUT_TOTAL = float(os.getenv("UNISDK_ASYNC_HTTP_TIMEOUT", "600"))
_DEFAULT_TIMEOUT_CONNECT = float(os.getenv("UNISDK_ASYNC_HTTP_CONNECT_TIMEOUT", "30"))
_DEFAULT_POOL_LIMIT = int(os.getenv("UNISDK_ASYNC_HTTP_POOL_LIMIT", "100"))


class RequestError(Exception):
    """Raised when an async HTTP response has a non-success status."""

    def __init__(self, url: str, r_type: str, status: int, body: str, /):
        super().__init__(
            f"{r_type}:{url} failed with status code {status}: {body}",
        )
        self.url = url
        self.method = r_type
        self.status = status
        self.body = body


class _TraceResponse:
    """Minimal response shape accepted by sync HTTP file-trace finalizers."""

    def __init__(
        self,
        *,
        status_code: int,
        headers: Dict[str, str],
        body_text: str,
        body_json: Any,
    ) -> None:
        self.status_code = status_code
        self.headers = headers
        self.text = body_text
        self._body_json = body_json

    def json(self) -> Any:
        if self._body_json is not None:
            return self._body_json
        raise ValueError("response body is not JSON")


_session: Optional[aiohttp.ClientSession] = None
_session_loop: Optional[asyncio.AbstractEventLoop] = None


def _client_timeout() -> aiohttp.ClientTimeout:
    return aiohttp.ClientTimeout(
        total=_DEFAULT_TIMEOUT_TOTAL,
        connect=_DEFAULT_TIMEOUT_CONNECT,
    )


async def _get_session() -> aiohttp.ClientSession:
    """Return a process-wide aiohttp session bound to the running event loop."""

    global _session, _session_loop

    loop = asyncio.get_running_loop()
    if _session is not None and not _session.closed and _session_loop is loop:
        return _session

    if _session is not None and not _session.closed:
        await _session.close()

    connector = aiohttp.TCPConnector(limit=_DEFAULT_POOL_LIMIT)
    _session = aiohttp.ClientSession(
        timeout=_client_timeout(),
        connector=connector,
    )
    _session_loop = loop
    return _session


async def close() -> None:
    """Close the shared async HTTP session (for tests / process shutdown)."""

    global _session, _session_loop
    if _session is not None and not _session.closed:
        await _session.close()
    _session = None
    _session_loop = None


async def request(
    method: str,
    url: str,
    *,
    raise_for_status: bool = True,
    params: Optional[Dict[str, Any]] = None,
    json: Optional[Any] = None,
    data: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[aiohttp.ClientTimeout | float] = None,
) -> Any:
    """Issue an async HTTP request with retry + backoff matching sync HTTP."""

    request_headers = dict(headers) if headers else {}
    if sync_http.is_otel_enabled():
        request_headers = sync_http._inject_trace_context(request_headers)

    request_kwargs: Dict[str, Any] = {
        "headers": request_headers,
        "params": params,
        "json": json,
        "data": data,
    }
    if timeout is not None:
        request_kwargs["timeout"] = (
            timeout
            if isinstance(timeout, aiohttp.ClientTimeout)
            else aiohttp.ClientTimeout(total=float(timeout))
        )

    pending_path = sync_http._write_pending_trace(method, url, request_kwargs)

    tracer = sync_http.get_tracer()
    route = sync_http._extract_route(url)
    span_name = f"{method} {route}"
    if tracer is not None:
        from opentelemetry.trace import SpanKind, Status, StatusCode

        span_cm = tracer.start_as_current_span(span_name, kind=SpanKind.CLIENT)
    else:
        span_cm = nullcontext()
        Status = StatusCode = None  # type: ignore[assignment]

    session = await _get_session()
    connect_retries_left = _DEFAULT_RETRY_CONNECT
    read_retries_left = _DEFAULT_RETRY_READ
    total_retries_left = _DEFAULT_RETRY_TOTAL
    attempt = 0
    start_time = time.monotonic()

    with span_cm as span:
        if span is not None:
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", url)
            span.set_attribute("http.route", route)

        while True:
            try:
                async with session.request(method, url, **request_kwargs) as resp:
                    body_text = await resp.text()
                    body_json: Any = None
                    if body_text:
                        try:
                            body_json = json_lib.loads(body_text)
                        except ValueError:
                            body_json = None

                    if resp.status in _RETRYABLE_STATUSES and total_retries_left > 0:
                        total_retries_left -= 1
                        attempt += 1
                        delay = _DEFAULT_BACKOFF_FACTOR * (2 ** (attempt - 1))
                        _logger.debug(
                            "Retrying %s %s (status=%d, attempt=%d, delay=%.2fs)",
                            method,
                            url,
                            resp.status,
                            attempt,
                            delay,
                        )
                        await asyncio.sleep(delay)
                        continue

                    duration_ms = int((time.monotonic() - start_time) * 1000)
                    trace_response = _TraceResponse(
                        status_code=resp.status,
                        headers=dict(resp.headers),
                        body_text=body_text,
                        body_json=body_json,
                    )

                    if span is not None:
                        span.set_attribute("http.status_code", resp.status)
                        span.set_attribute("http.duration_ms", duration_ms)
                        if resp.status >= 400:
                            span.set_status(Status(StatusCode.ERROR))
                        else:
                            span.set_status(Status(StatusCode.OK))

                    sync_http._finalize_trace(pending_path, trace_response, duration_ms)

                    if raise_for_status and resp.status >= 400:
                        raise RequestError(url, method, resp.status, body_text)

                    return body_json if body_json is not None else body_text

            except (
                aiohttp.ClientConnectionError,
                aiohttp.ServerDisconnectedError,
            ) as exc:
                if connect_retries_left > 0 and total_retries_left > 0:
                    connect_retries_left -= 1
                    total_retries_left -= 1
                    attempt += 1
                    delay = _DEFAULT_BACKOFF_FACTOR * (2 ** (attempt - 1))
                    _logger.debug(
                        "Retrying %s %s after connect error (%s, attempt=%d, delay=%.2fs)",
                        method,
                        url,
                        type(exc).__name__,
                        attempt,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                duration_ms = int((time.monotonic() - start_time) * 1000)
                if span is not None:
                    span.set_status(Status(StatusCode.ERROR, str(exc)))
                    span.set_attribute("error.type", type(exc).__name__)
                    span.set_attribute("error.message", str(exc))
                    span.set_attribute("http.duration_ms", duration_ms)
                sync_http._mark_trace_failed(pending_path, exc, duration_ms)
                raise

            except aiohttp.ClientPayloadError as exc:
                if read_retries_left > 0 and total_retries_left > 0:
                    read_retries_left -= 1
                    total_retries_left -= 1
                    attempt += 1
                    delay = _DEFAULT_BACKOFF_FACTOR * (2 ** (attempt - 1))
                    _logger.debug(
                        "Retrying %s %s after read error (%s, attempt=%d, delay=%.2fs)",
                        method,
                        url,
                        type(exc).__name__,
                        attempt,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                duration_ms = int((time.monotonic() - start_time) * 1000)
                if span is not None:
                    span.set_status(Status(StatusCode.ERROR, str(exc)))
                    span.set_attribute("error.type", type(exc).__name__)
                    span.set_attribute("error.message", str(exc))
                    span.set_attribute("http.duration_ms", duration_ms)
                sync_http._mark_trace_failed(pending_path, exc, duration_ms)
                raise

            except Exception as exc:
                duration_ms = int((time.monotonic() - start_time) * 1000)
                if span is not None and Status is not None:
                    span.set_status(Status(StatusCode.ERROR, str(exc)))
                    span.set_attribute("error.type", type(exc).__name__)
                    span.set_attribute("error.message", str(exc))
                    span.set_attribute("http.duration_ms", duration_ms)
                if not isinstance(exc, RequestError):
                    sync_http._mark_trace_failed(pending_path, exc, duration_ms)
                raise


async def get(
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Any:
    return await request("GET", url, params=params, **kwargs)


async def post(
    url: str,
    *,
    data: Optional[Any] = None,
    json: Optional[Any] = None,
    **kwargs: Any,
) -> Any:
    return await request("POST", url, data=data, json=json, **kwargs)


async def patch(
    url: str,
    *,
    data: Optional[Any] = None,
    json: Optional[Any] = None,
    **kwargs: Any,
) -> Any:
    return await request("PATCH", url, data=data, json=json, **kwargs)


async def delete(url: str, **kwargs: Any) -> Any:
    return await request("DELETE", url, **kwargs)
