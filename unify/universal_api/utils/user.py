from typing import Optional

from unify import BASE_URL
from unify.utils import http
from unify.utils.helpers import _check_response, _validate_api_key


def get_user_basic_info(*, api_key: Optional[str] = None):
    """
    Get basic information for the authenticated user.

    Args:
        api_key: If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        The basic information for the authenticated user.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = http.get(f"{BASE_URL}/user/basic-info", headers=headers)
    _check_response(response)
    return response.json()
