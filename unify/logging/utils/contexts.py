from typing import Dict, List, Optional, Union

from unify import BASE_URL
from unify.utils import _requests

from ...utils.helpers import (
    _check_response,
    _get_and_maybe_create_project,
    _validate_api_key,
)
from .logs import CONTEXT_WRITE

# Contexts #
# ---------#


def create_context(
    name: str,
    description: str = None,
    is_versioned: bool = True,
    allow_duplicates: bool = True,
    unique_column_ids: Optional[Union[List[str], str]] = None,
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> None:
    """
    Create a context.

    Args:
        name: Name of the context to create.

        description: Description of the context to create.

        is_versioned: Whether the context is tracked via version control.

        allow_duplicates: Whether to allow duplicates in the context.

        unique_column_ids: The names for any unique automatic integer ascending columns. Default is None.

        project: Name of the project the context belongs to.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A message indicating whether the context was successfully created.
    """
    api_key = _validate_api_key(api_key)
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if isinstance(unique_column_ids, str):
        unique_column_ids = [unique_column_ids]
    body = {
        "name": name,
        "description": description,
        "is_versioned": is_versioned,
        "allow_duplicates": allow_duplicates,
        "unique_column_ids": unique_column_ids,
    }
    response = _requests.post(
        BASE_URL + f"/project/{project}/contexts",
        headers=headers,
        json=body,
    )
    _check_response(response)
    return response.json()


def rename_context(
    name: str,
    new_name: str,
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> None:
    """
    Rename a context.

    Args:
        name: Name of the context to rename.

        new_name: New name of the context.

        project: Name of the project the context belongs to.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.
    """
    api_key = _validate_api_key(api_key)
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = _requests.patch(
        BASE_URL + f"/project/{project}/contexts/{name}/rename",
        headers=headers,
        json={"name": new_name},
    )
    _check_response(response)
    return response.json()


def get_context(
    name: str,
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Get information about a specific context including its versioning status and current version.

    Args:
        name: Name of the context to get.

        project: Name of the project the context belongs to.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.
    """
    api_key = _validate_api_key(api_key)
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = _requests.get(
        BASE_URL + f"/project/{project}/contexts/{name}",
        headers=headers,
    )
    _check_response(response)
    return response.json()


def get_contexts(
    project: Optional[str] = None,
    *,
    prefix: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Gets all contexts associated with a project, with the corresponding prefix.

    Args:
        prefix: Prefix of the contexts to get.

        project: Name of the project the artifacts belong to.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: Dictionary containing one or more key:value pairs that will be stored
        as artifacts.

    Returns:
        A message indicating whether the artifacts were successfully added.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    response = _requests.get(
        BASE_URL + f"/project/{project}/contexts",
        headers=headers,
    )
    _check_response(response)
    contexts = response.json()
    contexts = {context["name"]: context["description"] for context in contexts}
    if prefix:
        contexts = {
            context: description
            for context, description in contexts.items()
            if context.startswith(prefix)
        }
    return contexts


def delete_context(
    name: str,
    *,
    delete_children: bool = True,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> None:
    """
    Delete a context from the server.

    Args:
        name: Name of the context to delete.

        delete_children: Whether to delete child contexts (which share the same "/" separated prefix).

        project: Name of the project the context belongs to.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.
    """
    api_key = _validate_api_key(api_key)
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    # ToDo: remove this hack once this task [https://app.clickup.com/t/86c3kuch6] is done
    all_contexts = get_contexts(project, prefix=name)
    for ctx in all_contexts:
        response = _requests.delete(
            BASE_URL + f"/project/{project}/contexts/{ctx}",
            headers=headers,
        )
        _check_response(response)
    if all_contexts:
        return response.json()


def add_logs_to_context(
    log_ids: List[int],
    *,
    context: Optional[str] = None,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> None:
    """
    Add logs to a context.

    Args:
        log_ids: List of log ids to add to the context.

        context: Name of the context to add the logs to.

        project: Name of the project the logs belong to.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A message indicating whether the logs were successfully added to the context.
    """
    api_key = _validate_api_key(api_key)
    context = context if context else CONTEXT_WRITE.get()
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {
        "context_name": context,
        "log_ids": log_ids,
    }
    response = _requests.post(
        BASE_URL + f"/project/{project}/contexts/add_logs",
        headers=headers,
        json=body,
    )
    _check_response(response)
    return response.json()


def commit_context(
    name: str,
    commit_message: str,
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Creates a commit for a single context.

    Args:
        name: Name of the context to commit.
        commit_message: A description of the changes being saved.
        project: Name of the project the context belongs to.
        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing the new commit_hash.
    """
    api_key = _validate_api_key(api_key)
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {"commit_message": commit_message}
    response = _requests.post(
        BASE_URL + f"/project/{project}/contexts/{name}/commit",
        headers=headers,
        json=body,
    )
    _check_response(response)
    return response.json()


def rollback_context(
    name: str,
    commit_hash: str,
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Rolls back a single context to a specific commit.

    Args:
        name: Name of the context to roll back.
        commit_hash: The hash of the commit to restore.
        project: Name of the project the context belongs to.
        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A message indicating the success of the rollback operation.
    """
    api_key = _validate_api_key(api_key)
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {"commit_hash": commit_hash}
    response = _requests.post(
        BASE_URL + f"/project/{project}/contexts/{name}/rollback",
        headers=headers,
        json=body,
    )
    _check_response(response)
    return response.json()


def get_context_commits(
    name: str,
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[Dict]:
    """
    Retrieves the commit history for a context.

    Args:
        name: Name of the context.
        project: Name of the project the context belongs to.
        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A list of dictionaries, each representing a commit.
    """
    api_key = _validate_api_key(api_key)
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = _requests.get(
        BASE_URL + f"/project/{project}/contexts/{name}/commits",
        headers=headers,
    )
    _check_response(response)
    return response.json()
