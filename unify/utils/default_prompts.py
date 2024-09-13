import requests
from typing import Optional, Any, Dict

from unify import BASE_URL
from .helpers import _validate_api_key


def create_default_prompt(name: str, prompt: dict, api_key: Optional[str] = None):
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    url = f"{BASE_URL}/default_prompt"

    params = {
        "name": name,
        "prompt": prompt,
    }

    response = requests.post(url, headers=headers, json=params)
    response.raise_for_status()

    return response.json()


def get_default_prompt(name: str, api_key: Optional[str] = None):
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    url = f"{BASE_URL}/default_prompt"

    params = {
        "name": name,
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def delete_default_prompt(name: str, api_key: Optional[str] = None):
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    url = f"{BASE_URL}/default_prompt"

    params = {
        "name": name,
    }

    response = requests.delete(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def rename_default_prompt(name: str, new_name: str, api_key: Optional[str] = None):
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    url = f"{BASE_URL}/default_prompt/rename"

    params = {
        "name": name,
        "new_name": new_name,
    }

    response = requests.post(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def list_default_prompts(api_key: Optional[str] = None):
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    url = f"{BASE_URL}/default_prompt/list"

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()
