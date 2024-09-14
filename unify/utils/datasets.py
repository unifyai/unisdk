import json
import requests
from typing import List, Dict, Optional, Union

from unify import BASE_URL
from unify.types import Datum
from .helpers import _validate_api_key, _res_to_list


def _upload_dataset_from_str(
    name: str, content: str, api_key: Optional[str] = None
) -> str:
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    files = {"file": ("dataset", content, "application/x-jsonlines")}
    data = {"name": name}
    # Send POST request to the /dataset endpoint
    response = requests.post(
        BASE_URL + "/dataset", headers=headers, data=data, files=files
    )
    response.raise_for_status()
    return json.loads(response.text)["info"]


def upload_dataset_from_file(
    name: str, path: str, api_key: Optional[str] = None
) -> str:
    """
    Uploads a local file as a dataset to the platform.

    Args:
        name: Name given to the uploaded dataset.
        path: Path to the file to be uploaded.
        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        Info msg with the response from the HTTP endpoint.
    Raises:
        ValueError: If there was an HTTP error.
    """
    with open(path, "rb") as f:
        content_str = f.read().decode()
    return _upload_dataset_from_str(name, content_str, api_key)


def upload_dataset_from_dictionary(
    name: str, content: List[Dict[str, str]], api_key: Optional[str] = None
) -> str:
    """
    Uploads a list of dictionaries as a dataset to the platform.
    Each dictionary in the list must contain a `prompt` key.

    Args:
        name: Name given to the uploaded dataset.
        content: Path to the file to be uploaded.
        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        Info msg with the response from the HTTP endpoint.
    Raises:
        ValueError: If there was an HTTP error.
    """
    content_str = "\n".join([json.dumps(d) for d in content])
    return _upload_dataset_from_str(name, content_str, api_key)


def download_dataset(
    name: str, path: Optional[str] = None, api_key: Optional[str] = None
) -> Union[List[Datum], None]:
    """
    Downloads a dataset from the platform.

    Args:
        name: Name of the dataset to download.
        path: If specified, path to save the dataset.
        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        If path is not specified, returns the dataset content, if specified, returns
        None.
    Raises:
        ValueError: If there was an HTTP error.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    params = {"name": name}
    # Send GET request to the /dataset endpoint
    response = requests.get(BASE_URL + "/dataset", headers=headers, params=params)
    response.raise_for_status()
    if path:
        with open(path, "w+") as f:
            f.write("\n".join([json.dumps(d) for d in json.loads(response.text)]))
            return None
    ret = json.loads(response.text)
    return [Datum(
        **{k: v for k, v in item.items() if k not in ("id", "num_tokens", "timestamp")}
    ) for item in ret]


def delete_dataset(name: str, api_key: Optional[str] = None) -> str:
    """
    Deletes a dataset from the platform.

    Args:
        name: Name given to the uploaded dataset.
        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        str: Info msg with the response from the HTTP endpoint.
    Raises:
        ValueError: If there was an HTTP error.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    params = {"name": name}
    # Send DELETE request to the /dataset endpoint
    response = requests.delete(BASE_URL + "/dataset", headers=headers, params=params)
    response.raise_for_status()
    return json.loads(response.text)["info"]


def rename_dataset(name: str, new_name: str, api_key: Optional[str] = None):
    """
    Renames a dataset.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    params = {"name": name, "new_name": new_name}
    response = requests.post(
        BASE_URL + "/dataset/rename", headers=headers, params=params
    )
    return response.json()


def list_datasets(api_key: Optional[str] = None) -> List[str]:
    """
    Fetches a list of all uploaded datasets.

    Args:
        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        List with the names of the uploaded datasets.
    Raises:
        ValueError: If there was an HTTP error.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    # Send GET request to the /dataset/list endpoint
    response = requests.get(BASE_URL + "/dataset/list", headers=headers)
    response.raise_for_status()
    return _res_to_list(response)



def add_prompt(name: str, prompt_data: dict, api_key: Optional[str] = None):
    """
    Adds a prompt to a dataset.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {"name": name, "prompt_data": prompt_data}
    response = requests.post(
        BASE_URL + "/dataset/add_prompt", headers=headers, json=body
    )
    return response.json()


def delete_prompt(name: str, prompt_id: int, api_key: Optional[str] = None):
    """
    Delete a prompt from a dataset
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    params = {"name": name, "prompt_id": prompt_id}
    response = requests.delete(
        BASE_URL + "/dataset/delete_prompt", headers=headers, params=params
    )
    return response.json()

