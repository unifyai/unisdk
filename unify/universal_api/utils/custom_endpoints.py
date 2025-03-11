from typing import Any, Dict, List, Optional

from unify import BASE_URL
from unify.utils import _requests

from ...utils.helpers import _validate_api_key


def create_custom_endpoint(
    *,
    name: str,
    url: str,
    key_name: str,
    model_name: Optional[str] = None,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a custom endpoint for API calls.

    Args:
        name: Alias for the custom endpoint. This will be the name used to call the endpoint.
        url: Base URL of the endpoint being called. Must support the OpenAI format.
        key_name: Name of the API key that will be passed as part of the query.
        model_name: Name passed to the custom endpoint as model name. If not specified, it will default to the endpoint alias.
        provider: If the custom endpoint is for a fine-tuned model which is hosted directly via one of the supported providers,
                  then this argument should be specified as the provider used.
        api_key: If specified, unify API key to be used. Defaults to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing the response from the API.

    Raises:
        requests.HTTPError: If the API request fails.
        KeyError: If the UNIFY_KEY is not set and no api_key is provided.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    params = {
        "name": name,
        "url": url,
        "key_name": key_name,
    }

    if model_name:
        params["model_name"] = model_name
    if provider:
        params["provider"] = provider

    response = _requests.post(
        f"{BASE_URL}/custom_endpoint",
        headers=headers,
        params=params,
    )
    if response.status_code != 200:
        raise Exception(response.json())

    return response.json()


def delete_custom_endpoint(
    name: str,
    *,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Delete a custom endpoint.

    Args:
        name: Name of the custom endpoint to delete.
        api_key: If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing the response message.

    Raises:
        requests.HTTPError: If the API request fails.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{BASE_URL}/custom_endpoint"

    params = {"name": name}

    response = _requests.delete(url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(response.json())

    return response.json()


def rename_custom_endpoint(
    name: str,
    new_name: str,
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Rename a custom endpoint.

    Args:
        name: Name of the custom endpoint to be updated.
        new_name: New name for the custom endpoint.
        api_key: If specified, unify API key to be used. Defaults
                 to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing the response information.

    Raises:
        requests.HTTPError: If the API request fails.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{BASE_URL}/custom_endpoint/rename"

    params = {"name": name, "new_name": new_name}

    response = _requests.post(url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(response.json())

    return response.json()


def list_custom_endpoints(
    *,
    api_key: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    Get a list of custom endpoints for the authenticated user.

    Args:
        api_key: If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A list of dictionaries containing information about custom endpoints.
        Each dictionary has keys: 'name', 'mdl_name', 'url', and 'key'.

    Raises:
        requests.exceptions.RequestException: If the API request fails.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{BASE_URL}/custom_endpoint/list"

    response = _requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(response.json())

    return response.json()
