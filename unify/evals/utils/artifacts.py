import requests
from typing import Optional, Dict, Any
from ...utils.helpers import _validate_api_key, _get_and_maybe_create_project

from unify import BASE_URL


# Artifacts #
# ----------#


def add_project_artifacts(
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    """
    Creates one or more artifacts associated to a project. Artifacts are project-level
    metadata that don’t depend on other variables.

    Args:
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
    body = {"artifacts": kwargs}
    project = _get_and_maybe_create_project(project, api_key=api_key)
    response = requests.post(
        BASE_URL + f"/project/{project}/artifacts",
        headers=headers,
        json=body,
    )
    response.raise_for_status()
    return response.json()


def delete_project_artifact(
    key: str,
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """
    Deletes an artifact from a project.

    Args:
        project: Name of the project to delete an artifact from.

        key: Key of the artifact to delete.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        Whether the artifacts were successfully deleted.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    project = _get_and_maybe_create_project(project, api_key=api_key)
    response = requests.delete(
        BASE_URL + f"/project/{project}/artifacts/{key}",
        headers=headers,
    )
    response.raise_for_status()
    return response.json()


def get_project_artifacts(
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns the key-value pairs of all artifacts in a project.

    Args:
        project: Name of the project to delete an artifact from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A dictionary of all artifacts associated with the project, with keys for
        artifact names and values for the artifacts themselves.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    project = _get_and_maybe_create_project(project, api_key=api_key)
    response = requests.get(BASE_URL + f"/project/{project}/artifacts", headers=headers)
    response.raise_for_status()
    return response.json()
