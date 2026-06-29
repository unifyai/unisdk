from typing import Any, Dict, List, Literal, Optional

from unisdk import BASE_URL
from unisdk.utils import http
from unisdk.utils.helpers import _create_request_header

OrganizationInviteRoleName = Literal["Admin", "Member", "Viewer"]


def list_organizations(
    *,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List organizations visible to the authenticated user with role metadata.

    Args:
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        Organization membership records returned by the API.
    """
    headers = _create_request_header(api_key)
    response = http.get(
        f"{BASE_URL}/organizations",
        headers=headers,
    )
    return response.json()


def invite_org_member(
    organization_id: int,
    email: str,
    *,
    role_name: Optional[OrganizationInviteRoleName] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Invite a user to join an organization.

    Args:
        organization_id: The organization identifier.
        email: Invitee email address.
        role_name: Optional invite role (``Admin``, ``Member``, or ``Viewer``).
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        Invite response payload returned by the API.
    """
    headers = _create_request_header(api_key)
    payload: Dict[str, Any] = {"email": email}
    if role_name is not None:
        payload["role_name"] = role_name
    response = http.post(
        f"{BASE_URL}/organizations/{organization_id}/invites",
        headers=headers,
        json=payload,
    )
    return response.json()


def list_org_members(
    organization_id: int,
    *,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List the human members of an organization.

    Args:
        organization_id: The organization identifier.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        Organization member records returned by the API.
    """
    headers = _create_request_header(api_key)
    response = http.get(
        f"{BASE_URL}/organizations/{organization_id}/members",
        headers=headers,
    )
    return response.json()
