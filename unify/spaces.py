"""Space lifecycle helpers for the Unify SDK."""

from typing import Any, Dict, List, Optional

from unify import BASE_URL
from unify.utils import http
from unify.utils.helpers import _create_request_header


def _response_json_or_empty(response: Any) -> Any:
    """Return JSON response data, treating successful empty bodies as empty dicts."""
    if response.status_code == 204 or not response.content:
        return {}
    return response.json()


def create_space(
    *,
    name: str,
    description: str,
    organization_id: Optional[int] = None,
    owner_user_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a team space visible to the caller.

    Args:
        name: Display name for the space.
        description: Human-readable purpose and operating scope for the space.
        organization_id: Optional organization identifier for org-owned spaces.
        owner_user_id: Optional owner user identifier.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        The created space record.
    """
    headers = _create_request_header(api_key)
    body = {
        "name": name,
        "description": description,
        "organization_id": organization_id,
        "owner_user_id": owner_user_id,
    }
    body = {k: v for k, v in body.items() if v is not None}

    response = http.post(f"{BASE_URL}/spaces", headers=headers, json=body)
    return response.json()


def delete_space(
    space_id: int,
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Delete a space the caller can manage.

    Args:
        space_id: The space identifier.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        The API response payload, or an empty dict when the response has no body.
    """
    headers = _create_request_header(api_key)
    response = http.delete(f"{BASE_URL}/spaces/{space_id}", headers=headers)
    return _response_json_or_empty(response)


def update_space(
    space_id: int,
    patch: Dict[str, Any],
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update editable fields on a space.

    Args:
        space_id: The space identifier.
        patch: Space update fields to send to the API.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        The updated space record.
    """
    headers = _create_request_header(api_key)
    response = http.patch(
        f"{BASE_URL}/spaces/{space_id}",
        headers=headers,
        json=patch,
    )
    return response.json()


def add_space_member(
    space_id: int,
    assistant_id: Optional[int] = None,
    member_user_id: Optional[str] = None,
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Add an assistant or member-targeted personal coordinator to a space.

    Args:
        space_id: The space identifier.
        assistant_id: Optional assistant identifier.
        member_user_id: Optional organization member identifier. When supplied,
            the API resolves or provisions that member's personal Coordinator.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        Membership status information for the requested assistant.
    """
    has_assistant_id = assistant_id is not None
    normalized_member_user_id = (
        member_user_id.strip() if isinstance(member_user_id, str) else member_user_id
    )
    has_member_user_id = bool(normalized_member_user_id)
    if has_assistant_id == has_member_user_id:
        raise ValueError("Provide exactly one of assistant_id or member_user_id.")

    body: Dict[str, Any] = {}
    if assistant_id is not None:
        body["assistant_id"] = assistant_id
    if has_member_user_id:
        body["member_user_id"] = normalized_member_user_id

    headers = _create_request_header(api_key)
    response = http.post(
        f"{BASE_URL}/spaces/{space_id}/members",
        headers=headers,
        json=body,
    )
    return response.json()


def remove_space_member(
    space_id: int,
    assistant_id: int,
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Remove an assistant from a space.

    Args:
        space_id: The space identifier.
        assistant_id: The assistant identifier.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        The API response payload, or an empty dict when the response has no body.
    """
    headers = _create_request_header(api_key)
    response = http.delete(
        f"{BASE_URL}/spaces/{space_id}/members/{assistant_id}",
        headers=headers,
    )
    return _response_json_or_empty(response)


def list_spaces(
    *,
    organization_id: Optional[int] = None,
    owner_user_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List spaces visible to the caller.

    Args:
        organization_id: Optional organization filter.
        owner_user_id: Optional owner user filter.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        Space records visible to the caller.
    """
    headers = _create_request_header(api_key)
    params = {
        "organization_id": organization_id,
        "owner_user_id": owner_user_id,
    }
    params = {k: v for k, v in params.items() if v is not None}

    response = http.get(f"{BASE_URL}/spaces", headers=headers, params=params)
    return response.json()


def list_space_members(
    space_id: int,
    *,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List the live assistant members of a space.

    Args:
        space_id: The space identifier.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        Membership records for the space.
    """
    headers = _create_request_header(api_key)
    response = http.get(f"{BASE_URL}/spaces/{space_id}/members", headers=headers)
    return response.json()


def list_spaces_for_assistant(
    assistant_id: int,
    *,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List spaces where an assistant has a live membership.

    Args:
        assistant_id: The assistant identifier.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        Space records for the assistant.
    """
    headers = _create_request_header(api_key)
    response = http.get(
        f"{BASE_URL}/assistants/{assistant_id}/spaces",
        headers=headers,
    )
    return response.json()
