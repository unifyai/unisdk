from typing import Dict, List, Optional

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
    is_versioned: bool = False,
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> None:
    """
    Create a context.

    Args:
        name: Name of the context to create.

        description: Description of the context to create.

        is_versioned: Whether the context is versioned.

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
    body = {
        "name": name,
        "description": description,
        "is_versioned": is_versioned,
    }
    response = _requests.post(
        BASE_URL + f"/project/{project}/contexts",
        headers=headers,
        json=body,
    )
    _check_response(response)
    return response.json()


def get_contexts(
    *,
    prefix: Optional[str] = None,
    project: Optional[str] = None,
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
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> None:
    """
    Delete a context from the server.

    Args:
        name: Name of the context to delete.

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
    response = _requests.delete(
        BASE_URL + f"/project/{project}/contexts/{name}",
        headers=headers,
    )
    _check_response(response)
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
