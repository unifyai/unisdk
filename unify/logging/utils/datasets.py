from typing import Any, Dict, List, Optional

from ...utils.helpers import _get_and_maybe_create_project, _validate_api_key
from ..logs import Log
from .contexts import *
from .logs import *

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
    allow_duplicates: bool = False,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[int]:
    """
    Upload a dataset to the server.

    Args:
        name: Name of the dataset.

        data: Contents of the dataset.

        overwrite: Whether to overwrite the dataset if it already exists.

        allow_duplicates: Whether to allow duplicates in the dataset.

        project: Name of the project the dataset belongs to.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.
    Returns:
        A list all log ids in the dataset.
    """
    api_key = _validate_api_key(api_key)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = f"Datasets/{name}"
    log_instances = [isinstance(item, unify.Log) for item in data]
    are_logs = False
    if not allow_duplicates and not overwrite:
        # ToDo: remove this verbose logic once ignore_duplicates is implemented
        if name in unify.list_datasets():
            upstream_dataset = unify.Dataset(
                unify.download_dataset(name, project=project, api_key=api_key),
            )
        else:
            upstream_dataset = unify.Dataset([])
    if any(log_instances):
        assert all(log_instances), "If any items are logs, all items must be logs"
        are_logs = True
        # ToDo: remove this verbose logic once ignore_duplicates is implemented
        if not allow_duplicates and not overwrite:
            data = [l for l in data if l not in upstream_dataset]
    elif not all(isinstance(item, dict) for item in data):
        # ToDo: remove this verbose logic once ignore_duplicates is implemented
        if not allow_duplicates and not overwrite:
            data = [item for item in data if item not in upstream_dataset]
        data = [{"data": item} for item in data]
    if name in unify.list_datasets():
        upstream_ids = get_logs(
            project=project,
            context=context,
            return_ids_only=True,
        )
    else:
        upstream_ids = []
    if not are_logs:
        return upstream_ids + create_logs(
            project=project,
            context=context,
            entries=data,
            mutable=True,
            batched=True,
            # ToDo: uncomment once ignore_duplicates is implemented
            # ignore_duplicates=not allow_duplicates,
        )
    local_ids = [l.id for l in data]
    matching_ids = [id for id in upstream_ids if id in local_ids]
    matching_data = [l.entries for l in data if l.id in matching_ids]
    assert len(matching_data) == len(
        matching_ids,
    ), "matching data and ids must be the same length"
    if matching_data:
        update_logs(
            logs=matching_ids,
            api_key=api_key,
            entries=matching_data,
            overwrite=True,
        )
    if overwrite:
        upstream_only_ids = [id for id in upstream_ids if id not in local_ids]
        if upstream_only_ids:
            delete_logs(
                logs=upstream_only_ids,
                context=context,
                project=project,
                api_key=api_key,
            )
            upstream_ids = [id for id in upstream_ids if id not in upstream_only_ids]
    ids_not_in_dataset = [
        id for id in local_ids if id not in matching_ids and id is not None
    ]
    if ids_not_in_dataset:
        if context not in unify.get_contexts():
            unify.create_context(
                context,
                project=project,
                api_key=api_key,
            )
        unify.add_logs_to_context(
            log_ids=ids_not_in_dataset,
            context=context,
            project=project,
            api_key=api_key,
        )
    local_only_data = [l.entries for l in data if l.id is None]
    if local_only_data:
        return upstream_ids + create_logs(
            project=project,
            context=context,
            entries=local_only_data,
            mutable=True,
            batched=True,
        )
    return upstream_ids + ids_not_in_dataset


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
        batched=True,
    )
    return logs
