"""Managed Computer Use add-on helpers and pricing constants.

Orchestra's ``contact_type_costs`` table is authoritative for live pricing.
These constants mirror the current defaults for documentation and client UX.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Literal, Optional

from unisdk import BASE_URL
from unisdk.utils import http
from unisdk.utils.helpers import _create_request_header

ManagedDesktopMode = Literal["ubuntu", "windows"]

MANAGED_DESKTOP_UBUNTU_MONTHLY_USD = Decimal("50")
MANAGED_DESKTOP_WINDOWS_MONTHLY_USD = Decimal("75")


def enable_managed_desktop(
    assistant_id: int,
    desktop_mode: ManagedDesktopMode,
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Enable the paid Computer Use add-on for an assistant."""
    headers = _create_request_header(api_key)
    response = http.post(
        f"{BASE_URL}/assistant/{assistant_id}/managed-desktop",
        headers=headers,
        json={"desktop_mode": desktop_mode},
    )
    return response.json()["info"]


def disable_managed_desktop(
    assistant_id: int,
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Disable the Computer Use add-on and release the managed VM."""
    headers = _create_request_header(api_key)
    response = http.delete(
        f"{BASE_URL}/assistant/{assistant_id}/managed-desktop",
        headers=headers,
    )
    return response.json()["info"]


def get_managed_desktop_status(
    assistant_id: int,
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Return billing state and monthly cost for Computer Use."""
    headers = _create_request_header(api_key)
    response = http.get(
        f"{BASE_URL}/assistant/{assistant_id}/managed-desktop",
        headers=headers,
    )
    return response.json()["info"]
