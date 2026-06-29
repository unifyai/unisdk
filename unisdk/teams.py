"""Team lifecycle helpers for the Unify SDK."""

from typing import Any, Dict, List, Optional

from unisdk import BASE_URL
from unisdk.utils import http
from unisdk.utils.helpers import _create_request_header


def _response_json_or_empty(response: Any) -> Any:
    """Return JSON response data, treating successful empty bodies as empty dicts."""
    if response.status_code == 204 or not response.content:
        return {}
    return response.json()


def _normalize_team_record(team: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure team records expose a stable ``team_id`` field."""
    normalized = dict(team)
    team_id = normalized.get("team_id")
    if team_id is None:
        team_id = normalized.get("id")
    if team_id is not None:
        normalized["team_id"] = team_id
    return normalized


def create_team(
    organization_id: int,
    *,
    name: str,
    description: str,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create an organization team with shared-memory membership.

    Args:
        organization_id: Organization that owns the team.
        name: Display name for the team.
        description: Human-readable purpose and operating scope for the team.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        The created team record.
    """
    headers = _create_request_header(api_key)
    response = http.post(
        f"{BASE_URL}/organizations/{organization_id}/teams",
        headers=headers,
        json={"name": name, "description": description},
    )
    return _normalize_team_record(response.json())


def delete_team(
    organization_id: int,
    team_id: int,
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Delete a team the caller can manage.

    Args:
        organization_id: Organization that owns the team.
        team_id: The team identifier.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        The API response payload, or an empty dict when the response has no body.
    """
    headers = _create_request_header(api_key)
    response = http.delete(
        f"{BASE_URL}/organizations/{organization_id}/teams/{team_id}",
        headers=headers,
    )
    return _response_json_or_empty(response)


def update_team(
    organization_id: int,
    team_id: int,
    patch: Dict[str, Any],
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update editable fields on a team.

    Args:
        organization_id: Organization that owns the team.
        team_id: The team identifier.
        patch: Team update fields to send to the API.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        The updated team record.
    """
    headers = _create_request_header(api_key)
    response = http.patch(
        f"{BASE_URL}/organizations/{organization_id}/teams/{team_id}",
        headers=headers,
        json=patch,
    )
    return _normalize_team_record(response.json())


def add_team_member(
    organization_id: int,
    team_id: int,
    assistant_id: Optional[int] = None,
    member_user_id: Optional[str] = None,
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Add an assistant or organization member to a team.

    Args:
        organization_id: Organization that owns the team.
        team_id: The team identifier.
        assistant_id: Optional assistant identifier.
        member_user_id: Optional organization member identifier. When supplied,
            the API resolves or provisions that member's workspace coordinator.
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
        f"{BASE_URL}/organizations/{organization_id}/teams/{team_id}/assistant-members",
        headers=headers,
        json=body,
    )
    return response.json()


def remove_team_member(
    organization_id: int,
    team_id: int,
    assistant_id: int,
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Remove an assistant from a team.

    Args:
        organization_id: Organization that owns the team.
        team_id: The team identifier.
        assistant_id: The assistant identifier.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        The API response payload, or an empty dict when the response has no body.
    """
    headers = _create_request_header(api_key)
    response = http.delete(
        (
            f"{BASE_URL}/organizations/{organization_id}/teams/{team_id}"
            f"/assistant-members/{assistant_id}"
        ),
        headers=headers,
    )
    return _response_json_or_empty(response)


def list_teams(
    organization_id: int,
    *,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List teams in an organization visible to the caller.

    Args:
        organization_id: Organization whose teams should be listed.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        Team records visible to the caller.
    """
    headers = _create_request_header(api_key)
    response = http.get(
        f"{BASE_URL}/organizations/{organization_id}/teams",
        headers=headers,
    )
    return [_normalize_team_record(team) for team in response.json()]


def list_team_members(
    organization_id: int,
    team_id: int,
    *,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List the live assistant members of a team.

    Args:
        organization_id: Organization that owns the team.
        team_id: The team identifier.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        Membership records for the team.
    """
    headers = _create_request_header(api_key)
    response = http.get(
        (
            f"{BASE_URL}/organizations/{organization_id}/teams/{team_id}"
            "/assistant-members"
        ),
        headers=headers,
    )
    return response.json()


def list_teams_for_assistant(
    assistant_id: int,
    *,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List teams where an assistant has a live membership.

    Args:
        assistant_id: The assistant identifier.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        Team summary records for the assistant.
    """
    headers = _create_request_header(api_key)
    response = http.get(
        f"{BASE_URL}/assistants/{assistant_id}/teams",
        headers=headers,
    )
    return [_normalize_team_record(team) for team in response.json()]
