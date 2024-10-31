import json
from typing import Any, Dict, List, Optional, Union

import requests
from unify import BASE_URL

from ...utils.helpers import _validate_api_key, _get_and_maybe_create_project


def _maybe_prepend_project_name(name: str, api_key: Optional[str] = None) -> str:
    project = _get_and_maybe_create_project(required=False, api_key=api_key)
    if project is not None and project not in name:
        return f"{project}/{name}"
    return name


def upload_dataset(
    name: str,
    content: list,
    *,
    api_key: Optional[str] = None,
) -> str:
    """
    Uploads a dataset to the platform

    Args:
        name: The name of the dataset

        content: List of entries to upload

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.
    """
    api_key = _validate_api_key(api_key)
    name = _maybe_prepend_project_name(name, api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    data = {"name": name}
    # Create a dataset
    response = requests.post(
        BASE_URL + "/dataset",
        headers=headers,
        json=data,
    )
    response.raise_for_status()
    # Add the entries
    response = requests.post(
        BASE_URL + f"/dataset/{name}/entries",
        headers=headers,
        json={"entries": content},
    )
    response.raise_for_status()
    return response.json()


def download_dataset(
    name: str,
    *,
    path: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Optional[List[Any]]:
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
    name = _maybe_prepend_project_name(name, api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    # Send GET request to the /dataset endpoint
    response = requests.get(BASE_URL + f"/dataset/{name}", headers=headers)
    response.raise_for_status()
    if path:
        with open(path, "w+") as f:
            f.write("\n".join([json.dumps(d) for d in response.json()]))
            return None
    ret = response.json()
    return [{"id": e["id"], "entry": e["entry"]} for e in ret]


def delete_dataset(
    name: str,
    *,
    api_key: Optional[str] = None,
) -> str:
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
    name = _maybe_prepend_project_name(name, api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.delete(BASE_URL + f"/dataset/{name}", headers=headers)
    response.raise_for_status()
    return response.json()["info"]


def rename_dataset(
    name: str,
    new_name: str,
    *,
    api_key: Optional[str] = None,
):
    """
    Renames a dataset.

    Args:
        name: Current dataset name

        new_name: New name of the dataset

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    """
    api_key = _validate_api_key(api_key)
    name = _maybe_prepend_project_name(name, api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    data = {"new_name": new_name}
    response = requests.patch(
        BASE_URL + f"/dataset/{name}",
        headers=headers,
        data=data,
    )
    response.raise_for_status()
    return response.json()


def list_datasets(
    *,
    api_key: Optional[str] = None,
) -> List[str]:
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
    response = requests.get(BASE_URL + "/datasets/", headers=headers)
    response.raise_for_status()
    project = _get_and_maybe_create_project(required=False, api_key=api_key)
    if project is not None:
        return [
            item["name"].lstrip(project)[1:]
            for item in response.json()
            if project in item["name"]
        ]
    return [item["name"] for item in response.json()]


def add_dataset_entries(
    name: str,
    data: Union[Any, List[Any]],
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Union[str, List[int]]]:
    """
    Adds data to a dataset, and returns a list of ids and values for each of
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
    name = _maybe_prepend_project_name(name, api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if not isinstance(data, list):
        data = [data]
    response = requests.post(
        BASE_URL + f"/dataset/{name}/entries",
        headers=headers,
        json={"entries": data},
    )
    response.raise_for_status()
    return response.json()


def delete_dataset_entry(
    name: str,
    id: int,
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Union[str, List[int]]]:
    """
    Deletes data from a dataset by id, and returns a list of ids and values for each
    of those, split by those which were deleted and those which were not present.

    Args:
        name: The name of the dataset to delete the data from.

        id: Entry id

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A dict containing the info, and the ids for all entries deleted, split by those
        which were deleted and those which were not present.
    """
    api_key = _validate_api_key(api_key)
    name = _maybe_prepend_project_name(name, api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.delete(
        BASE_URL + f"/dataset/{name}/entry/{id}",
        headers=headers,
    )
    response.raise_for_status()
    return response.json()


# noinspection PyShadowingBuiltins
def get_dataset_entry(
    name: str,
    id: int,
    *,
    api_key: Optional[str] = None,
) -> List[Dict[str, Union[int, Any]]]:
    """
    Returns the specified dataset entry.

    Args:
        name: Dataset name.

        id: Entry id

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A dict containing the dataset entry.
    """
    api_key = _validate_api_key(api_key)
    name = _maybe_prepend_project_name(name, api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.get(
        BASE_URL + f"/dataset/{name}/entry/{id}",
        headers=headers,
    )
    response.raise_for_status()
    return response.json()


def download_dataset_artifacts(
    name: str,
    *,
    api_key: Optional[str] = None,
) -> Union[Dict[str, Any], None]:
    """
    Downloads a dataset from the platform.

    Args:
        name: Name of the dataset to download the artifacts for.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    """
    api_key = _validate_api_key(api_key)
    name = _maybe_prepend_project_name(name, api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.get(BASE_URL + f"/dataset/{name}/artifacts", headers=headers)
    response.raise_for_status()
    ret = response.json()
    return ret


def create_dataset_artifacts(
    name: str,
    artifacts: dict,
    *,
    api_key: Optional[str] = None,
) -> Union[List[Any], None]:
    """
    Downloads a dataset from the platform.

    Args:
        name: Name of the dataset to download the artifacts for.

        artifacts: A dict containing the artifacts to upload

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    """
    api_key = _validate_api_key(api_key)
    name = _maybe_prepend_project_name(name, api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    data = {"artifacts": artifacts}
    response = requests.post(
        BASE_URL + f"/dataset/{name}/artifacts",
        json=data,
        headers=headers,
    )
    response.raise_for_status()
    ret = response.json()
    return ret


def delete_dataset_artifact(
    name: str,
    key: str,
    *,
    api_key: Optional[str] = None,
) -> Union[List[Any], None]:
    """
    Deletes dataset artifact from the platform.

    Args:
        name: Name of the dataset to delete an artifact from.

        key: The key of the artifact to delete

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.
    """
    api_key = _validate_api_key(api_key)
    name = _maybe_prepend_project_name(name, api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.delete(
        BASE_URL + f"/dataset/{name}/artifacts/{key}",
        headers=headers,
    )
    response.raise_for_status()
    return response.json()
