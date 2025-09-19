from typing import Optional

from unify import BASE_URL
from unify.utils import http

from ...utils.helpers import _create_request_header, _res_to_list


def get_credits(*, api_key: Optional[str] = None) -> float:
    """
    Returns the credits remaining in the user account, in USD.

    Args:
        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        The credits remaining in USD.
    Raises:
        ValueError: If there was an HTTP error.
    """
    headers = _create_request_header(api_key)
    response = http.get(BASE_URL + "/credits", headers=headers)
    if response.status_code != 200:
        raise Exception(response.json())
    return _res_to_list(response)["credits"]
