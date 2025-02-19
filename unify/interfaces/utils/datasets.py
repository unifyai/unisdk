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
    overwrite: bool = False,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[int]:
    """
    Upload a dataset to the server.

    Args:
        name: Name of the dataset.

        data: Contents of the dataset.

        overwrite: Whether to overwrite the dataset if it already exists.

        project: Name of the project the dataset belongs to.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.
    Returns:
        A list of the newly created dataset logs.
    """
    api_key = _validate_api_key(api_key)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    log_instances = [isinstance(item, unify.Log) for item in data]
    are_logs = False
    if any(log_instances):
        assert all(log_instances), "If any items are logs, all items must be logs"
        are_logs = True
    elif not all(isinstance(item, dict) for item in data):
        data = [{"data": item} for item in data]
    if name in unify.list_datasets():
        upstream_ids = get_logs(
            project=project,
            context=f"Datasets/{name}",
            return_ids_only=True,
        )
    else:
        upstream_ids = []
    if not are_logs:
        return create_logs(
            project=project,
            context=f"Datasets/{name}",
            entries=data,
            mutable=True,
        )
    local_ids = [l.id for l in data]
    matching_ids = [id for id in upstream_ids if id in local_ids]
    matching_data = [l.entries for l in data if l.id in matching_ids]
    update_logs(
        logs=matching_ids,
        api_key=api_key,
        entries=matching_data,
        overwrite=True,
    )
    if overwrite:
        upstream_only_ids = [id for id in upstream_ids if id not in local_ids]
        delete_logs(
            logs=upstream_only_ids,
            project=project,
            api_key=api_key,
        )
    # ToDo add these existing logs to the dataset context
    ids_not_in_dataset = [
        id for id in local_ids if id not in matching_ids and id is not None
    ]
    # end ToDo
    local_only_data = [l.entries for l in data if l.id is None]
    ids = create_logs(
        project=project,
        context=f"Datasets/{name}",
        entries=local_only_data,
        mutable=True,
    )
    return ids


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
    logs = get_logs(
        project=project,
        context=f"Datasets/{name}",
    )
    return list(reversed(logs))


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


def add_dataset_entries(
    name: str,
    data: List[Any],
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[int]:
    """
    Adds entries to an existing dataset in the server.

    Args:
        name: Name of the dataset.

        contents: Contents to add to the dataset.

        project: Name of the project the dataset belongs to.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.
    Returns:
        A list of the newly added dataset logs.
    """
    api_key = _validate_api_key(api_key)
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    if not all(isinstance(item, dict) for item in data):
        data = [{"data": item} for item in data]
    logs = create_logs(
        project=project,
        context=f"Datasets/{name}",
        entries=data,
        mutable=True,
    )
    return logs
