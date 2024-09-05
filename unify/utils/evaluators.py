import requests
from typing import Optional, List, Any, Dict

from unify import BASE_URL
from .helpers import _validate_api_key


def create_evaluator(
    evaluator_config: Dict[str, Any], api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    Create a new evaluator based on the provided configuration.

    Args:
        evaluator_config: A dictionary containing the configuration for the evaluator.
        api_key: If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing information about the created evaluator.

    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{BASE_URL}/evaluator"

    response = requests.post(url, headers=headers, json=evaluator_config)
    response.raise_for_status()

    return response.json()


def get_evaluator(name: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the configuration of a specific evaluator.

    Args:
        name: Name of the evaluator to return the configuration of.
        api_key: If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing the evaluator configuration if successful.

    Raises:
        requests.HTTPError: If the API request fails.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{BASE_URL}/evaluator"

    params = {"name": name}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def delete_evaluator(name: str, api_key: Optional[str] = None) -> Dict[str, str]:
    """
    Delete an evaluator by its name.

    Args:
        name: Name of the evaluator to delete.
        api_key: If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing the response message if successful.

    Raises:
        requests.HTTPError: If the API request fails.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{BASE_URL}/evaluator"

    params = {"name": name}

    response = requests.delete(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def rename_evaluator(
    name: str, new_name: str, api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    Rename an existing evaluator.

    Args:
        name: Name of the evaluator to rename.
        new_name: New name for the evaluator.
        api_key: If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing the response message if successful.

    Raises:
        requests.HTTPError: If the API request fails.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{BASE_URL}/evaluator/rename"

    params = {"name": name, "new_name": new_name}

    response = requests.post(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def list_evaluators(api_key: Optional[str] = None) -> List[str]:
    """
    Get a list of available evaluators.

    Args:
        api_key: If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A list of available evaluator names if successful, otherwise an empty list.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{BASE_URL}/evaluator/list"
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()
