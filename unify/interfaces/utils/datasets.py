import requests
from typing import Optional, Dict, Any, List
from ...utils.helpers import _validate_api_key, _get_and_maybe_create_project

from unify import BASE_URL
from .contexts import *
from .logs import *
from ..logs import Log


# Datasets #
# ---------#


def list_datasets(
    *,
    project: Optional[str] = None,
    prefix: str = "",
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    List all datasets associated with a project and context.

    Args:
        project: Name of the project the datasets belong to.

        prefix: Prefix of the datasets to get.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A list of datasets.
    """
    api_key = _validate_api_key(api_key)
    contexts = get_contexts(
        prefix=f"Datasets/{prefix}",
        project=project,
        api_key=api_key,
    )
    return {
        "/".join(name.split("/")[1:]): description
        for name, description in contexts.items()
    }


def upload_dataset(
    name: str,
    data: List[Any],
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[Log]:
    """
    Upload a dataset to the server.

    Args:
        name: Name of the dataset.

        contents: Contents of the dataset.

        project: Name of the project the dataset belongs to.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.
    """
    api_key = _validate_api_key(api_key)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if not all(isinstance(item, dict) for item in data):
        data = [{name: item} for item in data]
    logs = create_logs(
        project=project,
        context=f"Datasets/{name}",
        entries=data,
        new=True,
        overwrite=True,
    )
    return logs


def download_dataset(
    name: str,
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[Log]:
    """
    Download a dataset from the server.

    Args:
        name: Name of the dataset.

        project: Name of the project the dataset belongs to.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.
    """
    api_key = _validate_api_key(api_key)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    logs = get_logs(
        project=project,
        context=f"Datasets/{name}",
    )
    return logs


def delete_dataset(
    name: str,
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> None:
    """
    Delete a dataset from the server.

    Args:
        name: Name of the dataset.

        project: Name of the project the dataset belongs to.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.
    """
    api_key = _validate_api_key(api_key)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    # ToDo: remove this once contexts correctly delete their logs
    log_ids = get_logs(
        project=project,
        context=f"Datasets/{name}",
        return_ids_only=True,
    )
    delete_logs(
        logs=log_ids,
        project=project,
        api_key=api_key,
    )
    # end ToDo
    delete_context(f"Datasets/{name}", project=project, api_key=api_key)
