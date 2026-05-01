from typing import Any, Dict, List, Optional

from unify import BASE_URL
from unify.utils import http
from unify.utils.helpers import _create_request_header


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
