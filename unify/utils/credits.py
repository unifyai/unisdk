import requests
from typing import Optional

from unify import BASE_URL
from .helpers import _validate_api_key, _res_to_list


def get_credits(api_key: Optional[str] = None) -> float:
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
    response = requests.get(BASE_URL + "/credits", headers=headers)
    response.raise_for_status()
    return _res_to_list(response)["credits"]


def promo_code():
    raise NotImplementedError
