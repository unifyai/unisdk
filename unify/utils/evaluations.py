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
    Create a new project with the given name.

    Args:
        name: The name of the new project.

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
        BASE_URL + "/log/project", headers=headers, json=body
    )
    response.raise_for_status()
    return response.json()


def rename_project(
        name: str,
        new_name: str,
        api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    Create a new project with the given name.

    Args:
        name: The old name of the project, to be changed.

        new_name: The new name for the project.

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
    params = {"name": name, "new_name": new_name}
    response = requests.put(
        BASE_URL + "/log/project/rename", headers=headers, params=params
    )
    response.raise_for_status()
    return response.json()


def delete_project(
        name: str,
        api_key: Optional[str] = None
) -> str:
    """
    Deletes the specified project.

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
    params = {"name": name}
    response = requests.delete(
        BASE_URL + "/log/project", headers=headers, params=params
    )
    response.raise_for_status()
    return response.json()


def list_projects(
        api_key: Optional[str] = None
) -> List[str]:
    """
    Fetches a list of all project names.

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
        BASE_URL + "/log/project/list", headers=headers
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
    Create a new set of artifacts for the project.

    Args:
        project: The name of the project to create the artifacts for.

        artifacts: The artifacts to add to the project.

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
    body = {"project": project, "artifacts": artifacts}
    response = requests.post(
        BASE_URL + "/log/artifact", headers=headers, json=body
    )
    response.raise_for_status()
    return response.json()


def delete_artifacts(
        project: str,
        artifacts: Union[str, List[str]],
        api_key: Optional[str] = None
) -> str:
    """
    Deletes the specified project.

    Args:
        project: The name of the project to delete artifacts from.

        artifacts: The artifact names to delete from the project.

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
    params = {"project": project, "artifacts": artifacts}
    response = requests.delete(
        BASE_URL + "/log/artifact", headers=headers, params=params
    )
    response.raise_for_status()
    return response.json()


def list_artifacts(
        project: str,
        api_key: Optional[str] = None
) -> List[str]:
    """
    Fetches a list of all artifacts for the given project.

    Args:
        project: The name of the project to delete artifacts from.

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
    params = {"project": project}
    response = requests.get(
        BASE_URL + "/log/artifact/list", headers=headers, params=params,
    )
    response.raise_for_status()
    return response.json()


# Logs #
# -----#

def log(
        project: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs
) -> int:
    """
    Returns the data (id and values) by querying the data based on their values.

    Args:
        project: The name of the project to log the data for. Inferred from globally set
        project if not specified.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: The key value pairs to log into the console as part of this log event.

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
    body = {"data": kwargs, "project": project}
    response = requests.post(
        BASE_URL + "/log", headers=headers, json=body
    )
    response.raise_for_status()
    return response.json()


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


def delete_logs(
        id: Union[int, List[int]],
        api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    The logs to delete.

    Args:
        id: The ids of the logs to delete.

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
    body = {"id": id}
    response = requests.delete(
        BASE_URL + "/log", headers=headers, json=body
    )
    response.raise_for_status()
    return response.json()


def delete_log_entries(
        keys: Union[str, List[str]],
        id: str,
        api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    Delete log entries based on their keys.

    Args:
        keys: The entry keys to delete from the specified log.

        id: The id of the log to delete entries from.

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
    body = {"keys": keys, "id": id}
    response = requests.delete(
        BASE_URL + "/log/entry", headers=headers, json=body
    )
    response.raise_for_status()
    return response.json()


def get_logs_by_id(
        id: Union[int, List[int]],
        api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve a set of logs based on the ids of the logs.

    Args:
        id: The ids of the logs to retrieve the data for.

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
    body = {"id": id}
    response = requests.get(
        BASE_URL + "/log/by-id", headers=headers, json=body
    )
    response.raise_for_status()
    return response.json()


def get_logs_by_project(
        project: str,
        filter: Optional[str] = None,
        api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve a set of logs based on the ids of the logs.

    Args:
        project: The name of the project to retrieve the logs for.

        filter: The filtering to apply to the various log values, expressed as a string,
        for example:
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
    body = {"project": project, "filter": filter}
    response = requests.get(
        BASE_URL + "/log/by-project", headers=headers, json=body
    )
    response.raise_for_status()
    return response.json()


def group_logs(
        project: str,
        group_by: str,
        api_key: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group logs based on equality of a specific key.

    Args:
        project: The id of the project to group the logs for.

        group_by: The key along which to perform the equality grouping.

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
    body = {"project": project, "group_by": group_by}
    response = requests.get(
        BASE_URL + "/log/group", headers=headers, json=body
    )
    response.raise_for_status()
    return response.json()


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
