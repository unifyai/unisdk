from typing import Optional

from unify import BASE_URL
from unify.utils import http
from unify.utils.helpers import _create_request_header


def get_user_basic_info(*, api_key: Optional[str] = None):
    """
    Get basic information for the authenticated user.

    Args:
        api_key: If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        The basic information for the authenticated user.
    """
    headers = _create_request_header(api_key)
    response = http.get(f"{BASE_URL}/user/basic-info", headers=headers)
    return response.json()
