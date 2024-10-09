import requests
from typing import Dict, Optional, Any, Union, List, Tuple

import unify
from unify import BASE_URL
from .helpers import _validate_api_key


# Projects #
# ---------#

def create_project(
        name: str,
        api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    Creates a logging project and adds this to your account. This project will have
    a set of logs associated with it.

    Args:
        name: A unique, user-defined name used when referencing the project.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A message indicating whether the project was created successfully.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {"name": name}
    response = requests.post(
        BASE_URL + "/project", headers=headers, json=body
    )
    response.raise_for_status()
    return response.json()


def rename_project(
        name: str,
        new_name: str,
        api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    Renames a project from `name` to `new_name` in your account.

    Args:
        name: Name of the project to rename.

        new_name: A unique, user-defined name used when referencing the project.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A message indicating whether the project was successfully renamed.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {"name": new_name}
    response = requests.patch(
        BASE_URL + f"/project/{name}", headers=headers, json=body
    )
    response.raise_for_status()
    return response.json()


def delete_project(
        name: str,
        api_key: Optional[str] = None
) -> str:
    """
    Deletes a project from your account.

    Args:
        name: Name of the project to delete.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        Whether the project was successfully deleted.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.delete(
        BASE_URL + f"/project/{name}", headers=headers
    )
    response.raise_for_status()
    return response.json()


def list_projects(
        api_key: Optional[str] = None
) -> List[str]:
    """
    Returns the names of all projects stored in your account.

    Args:
        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        List of all project names.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.get(
        BASE_URL + "/projects", headers=headers
    )
    response.raise_for_status()
    return response.json()


# Artifacts #
# ----------#

def create_artifacts(
        project: str,
        artifacts: Dict[str, str],
        api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    Creates one or more artifacts associated to a project. Artifacts are project-level
    metadata that don’t depend on other variables.

    Args:
        project: Name of the project the artifacts belong to.

        artifacts: Dictionary containing one or more key:value pairs that will be stored
        as artifacts.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A message indicating whether the artifacts were successfully added.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {"artifacts": artifacts}
    response = requests.post(
        BASE_URL + f"/project/{project}/artifacts", headers=headers, json=body
    )
    response.raise_for_status()
    return response.json()


def delete_artifacts(
        project: str,
        key: str,
        api_key: Optional[str] = None
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
    response = requests.delete(
        BASE_URL + f"/project/{project}/artifacts/{key}", headers=headers
    )
    response.raise_for_status()
    return response.json()


def list_artifacts(
        project: str,
        api_key: Optional[str] = None
) -> List[str]:
    """
    Returns the key-value pairs of all artifacts in a project.

    Args:
        project: Name of the project to delete an artifact from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        List of all artifacts associated with the project.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.get(
        BASE_URL + f"/project/{project}/artifacts", headers=headers
    )
    response.raise_for_status()
    return response.json()


# Logs #
# -----#

def log(
        project: Optional[str] = None,
        logs: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
) -> int:
    """
    Creates one or more logs associated to a project. Logs are LLM-call-level data
    that might depend on other variables. This method returns the id of the new
    stored log.

    Args:
        project: Name of the project the stored logs will be associated to.

        logs: Dictionary containing one or more key:value pairs that will be logged
        into the platform. Keys can have an optional version defined after a forward
        slash. E.g. `system_msg/v1`. If defined, these versions will be used when
        grouping results on a per-key basis. Values must be JSON serializable.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        The unique id of newly created log entry.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if project is None:
        project = unify.active_project
        if project is None:
            raise Exception(
                "No project specified in the arguments, and no globally set project "
                "either. A project must be passed in the argument, or set globally via "
                "unify.activate('project_name')")
        if project not in list_projects(api_key):
            create_project(project, api_key)
    body = {"project": project, "logs": logs}
    response = requests.post(
        BASE_URL + "/log", headers=headers, json=body
    )
    response.raise_for_status()
    return response.json()


# ToDo: endpoint not available yet
def update_log(
        data: Dict[str, Any],
        id: int,
        api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    Returns the data (id and values) by querying the data based on their values.

    Args:
        data: The data to log into the console.

        id: The log id to update with extra data.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A message indicating whether the log was successfully updated.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {"data": data, "id": id}
    response = requests.put(
        BASE_URL + "/log", headers=headers, json=body
    )
    response.raise_for_status()
    return response.json()


# ToDo: endpoint doesn't work with list of ids yet
def delete_logs(
        id: Union[int, List[int]],
        api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    Deletes logs from a project.

    Args:
        id: IDs of the log to delete from a project.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A message indicating whether the logs were successfully deleted.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.delete(
        BASE_URL + f"/log/{id}", headers=headers
    )
    response.raise_for_status()
    return response.json()


# ToDo: endpoint doesn't work with multiple keys yet
def delete_log_entries(
        entry: Union[str, List[str]],
        id: str,
        api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    Deletes entries from a log.

    Args:
        entry: Name of the entries to delete from a given log.

        id: ID of the log to delete an entry from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A message indicating whether the log entries were successfully deleted.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.delete(
        BASE_URL + f"/log/{id}/entry/{entry}", headers=headers
    )
    response.raise_for_status()
    return response.json()


# ToDo: endpoint doesn't work for multiple ids yet
def get_logs_by_id(
        id: Union[int, List[int]],
        api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Returns the log associated with a given id or set of ids.

    Args:
        id: IDs of the logs to fetch.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        The full set of log data.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.get(
        BASE_URL + f"/log/{id}", headers=headers
    )
    response.raise_for_status()
    return response.json()


def get_logs_by_project(
        project: str,
        filter: Optional[str] = None,
        api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Returns a list of filtered logs from a project.

    Args:
        project: Name of the project to get logs from.

        filter: Boolean string to filter logs, for example:
        "(temperature > 0.5 and (len(system_msg) < 100 or 'no' in usr_response))"

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        The full set of log data for the project, after optionally applying filtering.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    params = {"project": project, "filter": filter}
    response = requests.get(
        BASE_URL + "/logs", headers=headers, params=params
    )
    response.raise_for_status()
    return response.json()


def group_logs(
        project: str,
        key: str,
        api_key: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns a list of the different version/values of one entry within a given project
    based on its key.

    Args:
        project: Name of the project to get logs from.

        key: Name of the log entry to get distinct values from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A dict containing the grouped logs, with each key of the dict representing the
        version of the log key with equal values.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    params = {"project": project, "key": key}
    response = requests.get(
        BASE_URL + "/logs/groups", headers=headers, params=params
    )
    response.raise_for_status()
    return response.json()


# ToDo: endpoint not available yet
def get_log_metrics(
        project: str,
        metrics: Tuple[str],
        filter: Optional[str] = None,
        api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve a set of log metrics across a project, after applying the filtering.

    Args:
        project: The id of the project to retrieve the logs for.

        metrics: The reduction metrics to retrieve for the logs.

        filter: The filtering to apply to the various log values, expressed as a string,
        for example:
        "(temperature > 0.5 and (len(system_msg) < 100 or 'no' in usr_response))"

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        The full set of reduced log metrics for the project, after optionally applying
        the optional filtering.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {"project": project, "metrics": metrics, "filter": filter}
    response = requests.get(
        BASE_URL + "/log/by-project/metrics", headers=headers, json=body
    )
    response.raise_for_status()
    return response.json()
