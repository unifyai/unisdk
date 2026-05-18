from typing import Any, Dict, List, Optional

from unify import BASE_URL
from unify.utils import http
from unify.utils.helpers import _create_request_header


def invite_org_member(
    organization_id: int,
    email: str,
    *,
    role_name: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Invite a user to join an organization.

    Args:
        organization_id: The organization identifier.
        email: Invitee email address.
        role_name: Optional organization role name for the invite.
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
