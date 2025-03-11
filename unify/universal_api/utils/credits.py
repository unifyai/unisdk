from typing import Optional

from unify import BASE_URL
from unify.utils import _requests

from ...utils.helpers import _res_to_list, _validate_api_key


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
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    # Send GET request to the /get_credits endpoint
    response = _requests.get(BASE_URL + "/credits", headers=headers)
    if response.status_code != 200:
        raise Exception(response.json())
    return _res_to_list(response)["credits"]
