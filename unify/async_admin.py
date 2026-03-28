"""Async HTTP client for Orchestra admin endpoints.

Provides an ``AsyncAdminClient`` backed by ``aiohttp`` with connection pooling
and retry logic that mirrors the sync ``unify.utils.http`` session
(``Retry(total=5, connect=3, read=2, backoff_factor=0.1)``).

Typical usage from Unity's spending-limit hook::

    client = AsyncAdminClient(api_key=os.getenv("ORCHESTRA_ADMIN_KEY"))
    data = await client.get_assistant_spend(agent_id=123, month="2026-03")
    await client.close()

The client is designed for long-lived reuse within a single event loop.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional, Set

import aiohttp

from unify import BASE_URL

_logger = logging.getLogger(__name__)

_RETRYABLE_STATUSES: Set[int] = {500, 502, 503, 504}

_DEFAULT_RETRY_TOTAL = 5
_DEFAULT_RETRY_CONNECT = 3
_DEFAULT_RETRY_READ = 2
_DEFAULT_BACKOFF_FACTOR = 0.1
_DEFAULT_TIMEOUT = 5.0
_DEFAULT_POOL_LIMIT = 20


class AsyncAdminClient:
    """Async client for Orchestra ``/admin/*`` endpoints.

    Uses ``aiohttp`` with connection pooling and automatic retries to match
    the reliability characteristics of the sync ``unify.utils.http`` session.

    Parameters
    ----------
    base_url:
        Orchestra API base URL.  Defaults to ``unify.BASE_URL``
        (which reads ``ORCHESTRA_URL`` or falls back to production).
    api_key:
        Bearer token for admin auth (typically ``ORCHESTRA_ADMIN_KEY``).
    timeout:
        Per-attempt timeout in seconds.
    pool_limit:
        Maximum number of simultaneous connections in the pool.
    retry_total:
        Maximum number of retry attempts (across connect + read failures).
    retry_connect:
        Maximum connect-failure retries (subset of *retry_total*).
    retry_read:
        Maximum read-failure retries (subset of *retry_total*).
    backoff_factor:
        Base delay multiplied by ``2 ** attempt`` for exponential backoff.
    """

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        api_key: str,
        timeout: float = _DEFAULT_TIMEOUT,
        pool_limit: int = _DEFAULT_POOL_LIMIT,
        retry_total: int = _DEFAULT_RETRY_TOTAL,
        retry_connect: int = _DEFAULT_RETRY_CONNECT,
        retry_read: int = _DEFAULT_RETRY_READ,
        backoff_factor: float = _DEFAULT_BACKOFF_FACTOR,
    ) -> None:
        self._base_url = (base_url or BASE_URL).rstrip("/")
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "accept": "application/json",
            "Content-Type": "application/json",
        }
        self._retry_total = retry_total
        self._retry_connect = retry_connect
        self._retry_read = retry_read
        self._backoff_factor = backoff_factor
        self._pool_limit = pool_limit

        self._session: Optional[aiohttp.ClientSession] = None
        self._session_loop: Optional[asyncio.AbstractEventLoop] = None

    # -- session lifecycle ---------------------------------------------------

    def _get_session(self) -> aiohttp.ClientSession:
        loop = asyncio.get_running_loop()
        if (
            self._session is None
            or self._session.closed
            or self._session_loop is not loop
        ):
            connector = aiohttp.TCPConnector(limit=self._pool_limit)
            self._session = aiohttp.ClientSession(
                headers=self._headers,
                timeout=self._timeout,
                connector=connector,
            )
            self._session_loop = loop
        return self._session

    @property
    def closed(self) -> bool:
        return self._session is None or self._session.closed

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None
        self._session_loop = None

    # -- retry wrapper -------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Issue an HTTP request with retry + backoff.

        Retries on connection errors (up to *retry_connect*), read errors
        (up to *retry_read*), and responses with status in
        ``{500, 502, 503, 504}`` — mirroring the sync ``urllib3.Retry``
        configuration.
        """
        url = f"{self._base_url}{path}"
        session = self._get_session()

        connect_retries_left = self._retry_connect
        read_retries_left = self._retry_read
        total_retries_left = self._retry_total
        attempt = 0

        while True:
            try:
                async with session.request(
                    method,
                    url,
                    params=params,
                    json=json,
                ) as resp:
                    if resp.status in _RETRYABLE_STATUSES and total_retries_left > 0:
                        total_retries_left -= 1
                        attempt += 1
                        delay = self._backoff_factor * (2 ** (attempt - 1))
                        _logger.debug(
                            "Retrying %s %s (status=%d, attempt=%d, delay=%.2fs)",
                            method,
                            path,
                            resp.status,
                            attempt,
                            delay,
                        )
                        await asyncio.sleep(delay)
                        continue

                    if resp.status >= 400:
                        body = await resp.text()
                        raise AdminRequestError(
                            url=url,
                            method=method,
                            status=resp.status,
                            body=body,
                        )

                    return await resp.json()

            except (
                aiohttp.ClientConnectionError,
                aiohttp.ServerDisconnectedError,
            ) as exc:
                if connect_retries_left > 0 and total_retries_left > 0:
                    connect_retries_left -= 1
                    total_retries_left -= 1
                    attempt += 1
                    delay = self._backoff_factor * (2 ** (attempt - 1))
                    _logger.debug(
                        "Retrying %s %s after connect error (%s, attempt=%d, delay=%.2fs)",
                        method,
                        path,
                        type(exc).__name__,
                        attempt,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise

            except aiohttp.ClientPayloadError as exc:
                if read_retries_left > 0 and total_retries_left > 0:
                    read_retries_left -= 1
                    total_retries_left -= 1
                    attempt += 1
                    delay = self._backoff_factor * (2 ** (attempt - 1))
                    _logger.debug(
                        "Retrying %s %s after read error (%s, attempt=%d, delay=%.2fs)",
                        method,
                        path,
                        type(exc).__name__,
                        attempt,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise

    # -- spend endpoints -----------------------------------------------------

    async def get_assistant_spend(
        self,
        agent_id: int,
        month: str,
    ) -> Dict[str, Any]:
        return await self._request(
            "GET",
            f"/admin/assistant/{agent_id}/spend",
            params={"month": month},
        )

    async def get_user_spend(
        self,
        user_id: str,
        month: str,
    ) -> Dict[str, Any]:
        return await self._request(
            "GET",
            f"/admin/user/{user_id}/spend",
            params={"month": month},
        )

    async def get_member_spend(
        self,
        user_id: str,
        org_id: int,
        month: str,
    ) -> Dict[str, Any]:
        return await self._request(
            "GET",
            f"/admin/organization/{org_id}/members/{user_id}/spend",
            params={"month": month},
        )

    async def get_org_spend(
        self,
        org_id: int,
        month: str,
    ) -> Dict[str, Any]:
        return await self._request(
            "GET",
            f"/admin/organization/{org_id}/spend",
            params={"month": month},
        )

    # -- notification endpoint -----------------------------------------------

    async def notify_limit_reached(
        self,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        return await self._request(
            "POST",
            "/admin/spending-limit-reached",
            json=payload,
        )


class AdminRequestError(Exception):
    """Raised when an admin endpoint returns a non-retryable error (4xx etc.)."""

    def __init__(self, *, url: str, method: str, status: int, body: str) -> None:
        self.url = url
        self.method = method
        self.status = status
        self.body = body
        super().__init__(
            f"{method}:{url} failed with status {status}: {body}",
        )
