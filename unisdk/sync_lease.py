"""Client helpers for Orchestra exclusive sync leases."""

from __future__ import annotations

from typing import Any, Dict, Optional

from unisdk import BASE_URL
from unisdk.utils import http
from unisdk.utils.helpers import _create_request_header, _get_project, _validate_api_key


class SyncLeaseHeldError(RuntimeError):
    """Raised when another writer currently holds the requested lease."""

    def __init__(
        self,
        lease_key: str,
        *,
        held_by: str | None = None,
        expires_at: str | None = None,
        detail: Any = None,
    ) -> None:
        self.lease_key = lease_key
        self.held_by = held_by
        self.expires_at = expires_at
        self.detail = detail
        super().__init__(
            f"Sync lease held for {lease_key!r}"
            + (f" by {held_by!r}" if held_by else "")
            + (f" until {expires_at}" if expires_at else ""),
        )


def acquire_sync_lease(
    lease_key: str,
    holder: str,
    *,
    ttl_seconds: float = 300.0,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Acquire (or renew) an exclusive sync lease for ``lease_key``."""
    api_key = _validate_api_key(api_key)
    headers = _create_request_header(api_key)
    project_name = _get_project(project)
    try:
        response = http.post(
            f"{BASE_URL}/sync_lease/acquire",
            headers=headers,
            json={
                "project": project_name,
                "lease_key": lease_key,
                "holder": holder,
                "ttl_seconds": float(ttl_seconds),
            },
        )
    except http.RequestError as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status == 409:
            detail = None
            held_by = None
            expires_at = None
            try:
                detail = exc.response.json().get("detail")
            except Exception:
                detail = None
            if isinstance(detail, dict):
                held_by = detail.get("held_by")
                expires_at = detail.get("expires_at")
            raise SyncLeaseHeldError(
                lease_key,
                held_by=held_by,
                expires_at=expires_at,
                detail=detail,
            ) from exc
        raise
    return response.json()


def release_sync_lease(
    lease_key: str,
    holder: str,
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Release a previously acquired sync lease if still held by ``holder``."""
    api_key = _validate_api_key(api_key)
    headers = _create_request_header(api_key)
    project_name = _get_project(project)
    response = http.post(
        f"{BASE_URL}/sync_lease/release",
        headers=headers,
        json={
            "project": project_name,
            "lease_key": lease_key,
            "holder": holder,
        },
    )
    return response.json()
