from typing import Any, Dict, List, Optional

from unify import BASE_URL
from unify.utils import _requests

from ...utils.helpers import _validate_api_key


def create_custom_api_key(
    name: str,
    value: str,
    *,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Create a custom API key.

    Args:
        name: Name of the API key.
        value: Value of the API key.
        api_key: If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing the response information.

    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{BASE_URL}/custom_api_key"

    params = {"name": name, "value": value}

    response = _requests.post(url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(response.json())

    return response.json()


def get_custom_api_key(
    name: str,
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get the value of a custom API key.

    Args:
        name: Name of the API key to get the value for.
        api_key: If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing the custom API key information.

    Raises:
        requests.HTTPError: If the request fails.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{BASE_URL}/custom_api_key"
    params = {"name": name}

    response = _requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(response.json())

    return response.json()


def delete_custom_api_key(
    name: str,
    *,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Delete a custom API key.

    Args:
        name: Name of the custom API key to delete.
        api_key: If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing the response message if successful.

    Raises:
        requests.HTTPError: If the API request fails.
        KeyError: If the API key is not found.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{BASE_URL}/custom_api_key"

    params = {"name": name}

    response = _requests.delete(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        raise KeyError("API key not found.")
    else:
        if response.status_code != 200:
            raise Exception(response.json())


def rename_custom_api_key(
    name: str,
    new_name: str,
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Rename a custom API key.

    Args:
        name: Name of the custom API key to be updated.
        new_name: New name for the custom API key.
        api_key: If specified, unify API key to be used. Defaults
                 to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing the response information.

    Raises:
        requests.HTTPError: If the API request fails.
        KeyError: If the API key is not provided or found in environment variables.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{BASE_URL}/custom_api_key/rename"

    params = {"name": name, "new_name": new_name}

    response = _requests.post(url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(response.json())

    return response.json()


def list_custom_api_keys(
    *,
    api_key: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    Get a list of custom API keys associated with the user's account.

    Args:
        api_key: If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A list of dictionaries containing custom API key information.
        Each dictionary has 'name' and 'value' keys.

    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{BASE_URL}/custom_api_key/list"

    response = _requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(response.json())

    return response.json()
