import json
from typing import Any, Dict, List, Optional, Union

import requests
from unify import BASE_URL

from .helpers import _res_to_list, _validate_api_key


def _upload_dataset_from_str(
    name: str,
    content: str,
    api_key: Optional[str] = None,
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
        BASE_URL + "/dataset",
        headers=headers,
        data=data,
        files=files,
    )
    response.raise_for_status()
    return json.loads(response.text)


def upload_dataset_from_file(
    name: str,
    path: str,
    api_key: Optional[str] = None,
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
    name: str,
    content: List[Dict[str, str]],
    api_key: Optional[str] = None,
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
    name: str,
    path: Optional[str] = None,
    raw_return: bool = False,
    api_key: Optional[str] = None,
) -> Union[List[Any], None]:
    """
    Downloads a dataset from the platform.

    Args:
        name: Name of the dataset to download.
        path: If specified, path to save the dataset.
        raw_return: Whether to provide the raw return, with extra meta-data.
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
    if raw_return:
        return ret
    return [
        {k: v for k, v in item.items() if k not in ("id", "timestamp")} for item in ret
    ]


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
        BASE_URL + "/dataset/rename",
        headers=headers,
        params=params,
    )
    response.raise_for_status()
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


def add_data_by_value(
    name: str,
    data: Union[Any, List[Any]],
    api_key: Optional[str] = None,
) -> Dict[str, Union[str, List[int]]]:
    """
    Adds data to a dataset by value, and returns a list of ids and values for each of
    those, split by those which were already present and those which were newly added.

    Args:
        name: The name of the dataset to add the data to.

        data: The data to add to the user account.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A dict containing the info, and the ids for all entries added, split by those
        which were added and those which were already present.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {"name": name, "data": data}
    response = requests.post(
        BASE_URL + "/dataset/data/by_value",
        headers=headers,
        json=body,
    )
    response.raise_for_status()
    return response.json()


def add_data_by_id(
    name: str,
    data: Union[int, List[int]],
    api_key: Optional[str] = None,
) -> Dict[str, Union[str, List[int]]]:
    """
    Adds data to a dataset by id, and returns a list of ids and values for each of
    those, split by those which were already present and those which were newly added.

    Args:
        name: The name of the dataset to add the data to.

        data: The data to add to the user account.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A dict containing the info, and the ids for all entries added, split by those
        which were added and those which were already present.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {"name": name, "data": data}
    response = requests.post(
        BASE_URL + "/dataset/data/by_id",
        headers=headers,
        json=body,
    )
    response.raise_for_status()
    return response.json()


def delete_data_by_value(
    name: str,
    data: Union[Any, List[Any]],
    api_key: Optional[str] = None,
) -> Dict[str, Union[str, List[int]]]:
    """
    Deletes data from a dataset by value, and returns a list of ids and values for each
    of those, split by those which were deleted and those which were not present.

    Args:
        name: The name of the dataset to delete the data from.

        data: The data to delete from the dataset.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A dict containing the info, and the ids for all entries deleted, split by those
        which were deleted and those which were not present.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if isinstance(data, list) and not data:
        return {"info": "data argument was empty. Nothing to delete."}
    params = {"name": name, "data": data}
    response = requests.delete(
        BASE_URL + "/dataset/data/by_value",
        headers=headers,
        params=params,
    )
    response.raise_for_status()
    return response.json()


def delete_data_by_id(
    name: str,
    data: Union[int, List[int]],
    api_key: Optional[str] = None,
) -> Dict[str, Union[str, List[int]]]:
    """
    Deletes data from a dataset by id, and returns a list of ids and values for each
    of those, split by those which were deleted and those which were not present.

    Args:
        name: The name of the dataset to delete the data from.

        data: The data to delete from the dataset.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A dict containing the info, and the ids for all entries deleted, split by those
        which were deleted and those which were not present.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if isinstance(data, list) and not data:
        return {"info": "data argument was empty. Nothing to delete."}
    params = {"name": name, "data": data}
    response = requests.delete(
        BASE_URL + "/dataset/data/by_id",
        headers=headers,
        params=params,
    )
    response.raise_for_status()
    return response.json()


def get_data_by_value(
    data: Union[Any, List[Any]],
    api_key: Optional[str] = None,
) -> List[Dict[str, Union[int, Any]]]:
    """
    Returns the data (id and values) by querying the data based on their unique ids.

    Args:
        data: The data to retrieve the contents for.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A list of dicts containing the id and the value.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {"data": data}
    response = requests.get(
        BASE_URL + "/dataset/data/by_value",
        headers=headers,
        json=body,
    )
    response.raise_for_status()
    return response.json()


def get_data_by_id(
    data: Union[int, List[int]],
    api_key: Optional[str] = None,
) -> List[Dict[str, Union[int, Any]]]:
    """
    Returns the data (id and values) by querying the data based on their values.

    Args:
        data: The data to retrieve the contents for.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A list of dicts containing the id and the value.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {"data": data}
    response = requests.get(
        BASE_URL + "/dataset/data/by_id",
        headers=headers,
        json=body,
    )
    response.raise_for_status()
    return response.json()
