from __future__ import annotations

import inspect
import functools
import threading
from contextvars import ContextVar
from typing import Any, Dict, List, Optional, Union

import requests
import unify
from unify import BASE_URL

from ..types import _Formatted
from .helpers import _validate_api_key

PROJECT_LOCK = threading.Lock()

# Helpers #
# --------#

# trace
current_global_active_log = ContextVar("current_global_active_log", default=None)

# Context
current_global_active_log_kwargs = ContextVar(
    "current_global_active_kwargs",
    default={},
)
current_logged_logs = ContextVar("current_logged_logs_ids", default={})
current_context_nest_level = ContextVar("current_context_nest_level", default=0)


def _get_and_maybe_create_project(project: str, api_key: Optional[str] = None) -> str:
    api_key = _validate_api_key(api_key)
    if project is None:
        project = unify.active_project
        if project is None:
            raise Exception(
                "No project specified in the arguments, and no globally set project "
                "either. A project must be passed in the argument, or set globally via "
                "unify.activate('project_name')",
            )
    PROJECT_LOCK.acquire()
    if project not in list_projects(api_key):
        create_project(project, api_key)
    PROJECT_LOCK.release()
    return project


def _enclose_str(v):
    return f'"{v}"' if isinstance(v, str) else v


def _versioned_field(field_name: str):
    if "/" not in field_name:
        return False
    split = field_name.split("/")
    assert len(split) == 2, (
        "field name can have at most one / character, "
        "reserved for identifying versions in the appending string"
    )
    return True


# Projects #
# ---------#


def create_project(name: str, api_key: Optional[str] = None) -> Dict[str, str]:
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
    response = requests.post(BASE_URL + "/project", headers=headers, json=body)
    response.raise_for_status()
    return response.json()


def rename_project(
    name: str,
    new_name: str,
    api_key: Optional[str] = None,
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
    response = requests.patch(BASE_URL + f"/project/{name}", headers=headers, json=body)
    response.raise_for_status()
    return response.json()


def delete_project(name: str, api_key: Optional[str] = None) -> str:
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
    response = requests.delete(BASE_URL + f"/project/{name}", headers=headers)
    response.raise_for_status()
    return response.json()


def list_projects(api_key: Optional[str] = None) -> List[str]:
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
    response = requests.get(BASE_URL + "/projects", headers=headers)
    response.raise_for_status()
    return response.json()


# Artifacts #
# ----------#


def add_artifacts(
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
    project = _get_and_maybe_create_project(project, api_key)
    response = requests.post(
        BASE_URL + f"/project/{project}/artifacts",
        headers=headers,
        json=body,
    )
    response.raise_for_status()
    return response.json()


def delete_artifact(
    key: str,
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
    project = _get_and_maybe_create_project(project, api_key)
    response = requests.delete(
        BASE_URL + f"/project/{project}/artifacts/{key}",
        headers=headers,
    )
    response.raise_for_status()
    return response.json()


def get_artifacts(
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
    project = _get_and_maybe_create_project(project, api_key)
    response = requests.get(BASE_URL + f"/project/{project}/artifacts", headers=headers)
    response.raise_for_status()
    return response.json()


# Logs #
# -----#


class Log(_Formatted):

    def __init__(
        self,
        id: int,
        api_key: Optional[str] = None,
        **kwargs,
    ):
        self._api_key = _validate_api_key(api_key)
        self._entries = kwargs
        self._id = id

    # Properties

    @property
    def id(self) -> int:
        return self._id

    @property
    def entries(self) -> Dict[str, Any]:
        return self._entries

    # Dunders

    def __eq__(self, other: Union[dict, Log]) -> bool:
        if isinstance(other, dict):
            other = Log(other["id"], **other["entries"])
        return self._id == other._id

    def __len__(self):
        return len(self._entries)

    def __rich_repr__(self) -> List[Any]:
        """
        Used by the rich package for representing and print the instance.
        """
        for k, v in self._entries.items():
            yield k, v

    # Public

    def download(self):
        self._entries = get_log_by_id(self._id, self._api_key)._entries

    def add_entries(self, **kwargs) -> None:
        add_log_entries(self._id, self._api_key, **kwargs)
        self._entries = {**self._entries, **kwargs}

    def replace_entries(self, **kwargs) -> None:
        replace_log_entries(self._id, self._api_key, **kwargs)
        self._entries = {**self._entries, **kwargs}

    def update_entries(self, fn, **kwargs) -> None:
        update_log_entries(fn, self._id, self._api_key, **kwargs)
        for k, v in kwargs.items():
            self._entries[k] = fn(self._entries[k], v)

    def rename_entries(self, **kwargs) -> None:
        rename_log_entries(self._id, self._api_key, **kwargs)
        for old_name, new_name in kwargs.items():
            self._entries[new_name] = self._entries[old_name]
            del self._entries[old_name]

    def version_entries(self, **kwargs) -> None:
        version_log_entries(self._id, self._api_key, **kwargs)
        for field_name, version in kwargs.items():
            new_name = f"{field_name}/{version}"
            self._entries[new_name] = self._entries[field_name]
            del self._entries[field_name]

    def delete_entries(
        self,
        keys_to_delete: List[str],
    ) -> None:
        for key in keys_to_delete:
            delete_log_entry(key, self._id, self._api_key)
            del self._entries[key]

    def delete(self) -> None:
        delete_log(self._id, self._api_key)


def log(
    project: Optional[str] = None,
    version: Optional[Dict[str, str]] = None,
    skip_duplicates: bool = True,
    api_key: Optional[str] = None,
    **kwargs,
) -> Log:
    """
    Creates one or more logs associated to a project. Logs are LLM-call-level data
    that might depend on other variables. This method returns the id of the new
    stored log.

    Args:
        project: Name of the project the stored logs will be associated to.

        version: Optional version parameters which are associated with each key being
        logged, with the keys of this version dict being the keys being logged, and the
        values being the name of this particular version.

        skip_duplicates: Whether to skip creating new log entries for identical log
        data. If True (default), then the same eval Python script can be repeatedly run
        without duplicating the logged data every time. If False, then repeat entries
        will be added with identical data, but unique timestamps.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: Dictionary containing one or more key:value pairs that will be logged
        into the platform.

    Returns:
        The unique id of newly created log entry.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if version:
        kwargs = {
            k + "/" + version[k] if k in version else k: v for k, v in kwargs.items()
        }
    kwargs = {**kwargs, **current_global_active_log_kwargs.get()}
    project = _get_and_maybe_create_project(project, api_key)
    if skip_duplicates:
        retrieved_logs = get_logs_by_value(project, **kwargs, api_key=api_key)
        if retrieved_logs:
            return retrieved_logs[0]
    body = {"project": project, "entries": kwargs}
    response = requests.post(BASE_URL + "/log", headers=headers, json=body)
    response.raise_for_status()
    created_log = Log(response.json(), api_key, **kwargs)
    if current_context_nest_level.get() > 0:
        current_logged_logs.set(
            {
                **current_logged_logs.get(),
                created_log.id: list(current_global_active_log_kwargs.get().keys()),
            },
        )
    return created_log


def add_log_entries(
    id: Optional[int] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    """
    Add extra entries into an existing log.

    Args:
        id: The log id to update with extra data. Looks for the current active log if no id is provided.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: The data to log into the console.

    Returns:
        A message indicating whether the log was successfully updated.
    """
    current_active_log: Log = current_global_active_log.get()
    if current_active_log is None and id is None:
        raise ValueError(
            "`id` must be set if no current log is active within the context.",
        )
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if current_context_nest_level.get() > 0:

        kwargs = {
            **kwargs,
            **{
                k: v
                for k, v in current_global_active_log_kwargs.get().items()
                if k not in current_logged_logs.get().get(id, {})
            },
        }
    body = {"entries": {**kwargs, **current_global_active_log_kwargs.get()}}
    # ToDo: remove this once duplicates are prevented in the backend
    current_keys = get_log_by_id(id if id else current_active_log.id).entries.keys()
    assert not any(key in body["entries"] for key in current_keys), (
        "Duplicate keys detected, please use replace_log_entries or "
        "update_log_entries if you want to replace or modify an existing key."
    )
    # End ToDo
    response = requests.put(
        BASE_URL + f"/log/{id if id else current_active_log.id}",
        headers=headers,
        json=body,
    )
    response.raise_for_status()
    return response.json()


def delete_log(
    id: Union[int, List[int]],
    api_key: Optional[str] = None,
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
    response = requests.delete(BASE_URL + f"/log/{id}", headers=headers)
    response.raise_for_status()
    return response.json()


def delete_log_entry(
    entry: str,
    id: int,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Deletes an entry from a log.

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
    response = requests.delete(BASE_URL + f"/log/{id}/entry/{entry}", headers=headers)
    response.raise_for_status()
    return response.json()


def replace_log_entries(
    id: Optional[int] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    """
    Replaces existing entries in an existing log.

    Args:
        id: The log id to replace fields for. Looks for the current active log if no
        id is provided.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: The data to update in the log.

    Returns:
        A message indicating whether the log was successfully updated.
    """
    api_key = _validate_api_key(api_key)
    for k, v in kwargs.items():
        delete_log_entry(k, id, api_key)
    return add_log_entries(id, api_key, **kwargs)


def update_log_entries(
    fn: Union[callable, Dict[str, callable]],
    id: Optional[int] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    """
    Updates existing entries in an existing log.

    Args:
        fn: The function or set of functions to apply to each field in the log.

        id: The log id to update fields for. Looks for the current active log if no
        id is provided.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: The data to update in the log.

    Returns:
        A message indicating whether the log was successfully updated.
    """
    data = get_log_by_id(id, api_key).entries
    replacements = dict()
    for k, v in kwargs.items():
        f = fn[k] if isinstance(fn, dict) else fn
        replacements[k] = f(data[k], v)
    return replace_log_entries(id, api_key, **replacements)


def rename_log_entries(
    id: Optional[int] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    """
    Renames the set of log entries.

    Args:
        id: The log id to update the field names for. Looks for the current active log
        if no id is provided.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: The field names to update in the log, with keys as old names and values
        as new names.

    Returns:
        A message indicating whether the log field names were successfully updated.
    """
    api_key = _validate_api_key(api_key)
    data = get_log_by_id(id, api_key).entries
    for old_name in kwargs.keys():
        delete_log_entry(old_name, id, api_key)
    new_entries = {new_name: data[old_name] for old_name, new_name in kwargs.items()}
    return add_log_entries(id, api_key, **new_entries)


def version_log_entries(
    id: Optional[int] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    """
    Assigns versions to the set of log entries.

    Args:
        id: The log id to version the field names for. Looks for the current active log
        if no id is provided.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: The field names and versions to update in the log, with keys as field
        names and values as versions representing the versions, of either str or int
        type, with the latter being cast to a string.

    Returns:
        A message indicating whether the log fields were successfully versioned.
    """
    assert not any(_versioned_field(k) for k in kwargs.keys()), (
        "Cannot version a log entry which is already versioned. Use "
        "reversion_log_entries if you would like to change the version."
    )
    kwargs = {k: f"{k}/{v}" for k, v in kwargs.items()}
    return rename_log_entries(id, api_key, **kwargs)


def get_logs(
    project: Optional[str] = None,
    filter: Optional[str] = None,
    limit: Optional[int] = 100,
    offset: Optional[int] = None,
    api_key: Optional[str] = None,
) -> List[Log]:
    """
    Returns a list of filtered logs from a project.

    Args:
        project: Name of the project to get logs from.

        filter: Boolean string to filter logs, for example:
        "(temperature > 0.5 and (len(system_msg) < 100 or 'no' in usr_response))"

        limit: The number of logs to return.

        offset: The offset to start returning logs from.

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
    project = _get_and_maybe_create_project(project, api_key)
    params = {
        "project": project,
        "filter_expr": filter,
    }
    if limit:
        params["limit"] = limit
    if offset:
        params["offset"] = offset
    response = requests.get(BASE_URL + "/logs", headers=headers, params=params)
    response.raise_for_status()
    return [
        Log(dct["id"], **dct["entries"], api_key=api_key) for dct in response.json()
    ]


def get_log_by_id(id: int, api_key: Optional[str] = None) -> Log:
    """
    Returns the log associated with a given id.

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
    response = requests.get(BASE_URL + f"/log/{id}", headers=headers)
    response.raise_for_status()
    return Log(id, **response.json()["entries"])


def get_logs_by_value(
    project: str,
    api_key: Optional[str] = None,
    **kwargs,
) -> List[Log]:
    """
    Returns the logs with the data matching exactly if it exists,
    otherwise returns None.

    Args:
        project: Name of the project to get logs from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: The data to search the upstream logs for.

    Returns:
        The list of Logs which match the data, if any exist.
    """
    filter_str = " and ".join(
        [f"({k} == {_enclose_str(v)})" for k, v in kwargs.items()],
    )
    return get_logs(project, filter_str, api_key=api_key)


def get_log_by_value(
    project: str,
    api_key: Optional[str] = None,
    **kwargs,
) -> Optional[Log]:
    """
    Returns the log with the data matching exactly if it exists,
    otherwise returns None.

    Args:
        project: Name of the project to get logs from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: The data to search the upstream logs for.

    Returns:
        The single Log which matches the data, if it exists.
    """
    logs = get_logs_by_value(project, **kwargs, api_key=api_key)
    assert len(logs) in (
        0,
        1,
    ), "Expected exactly zero or one log, but found {len(logs)}"
    return logs[0] if logs else None


def get_groups(
    key: str,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns a list of the different version/values of one entry within a given project
    based on its key.

    Args:
        key: Name of the log entry to do equality matching for.

        project: Name of the project to get logs from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A dict containing the grouped logs, with each key of the dict representing the
        version of the log key with equal values, and the value being the equal value.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    project = _get_and_maybe_create_project(project, api_key)
    params = {"project": project, "key": key}
    response = requests.get(BASE_URL + "/logs/groups", headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def group_logs(key: str, project: Optional[str] = None, api_key: Optional[str] = None):
    """
    Groups logs based on equality '==' of the values for the specified key, returning a
    dict with group indices as the keys and the list of logs as the values. If the keys
    are not versioned, then the indices are simply incrementing integers.

    Args:
        key: Name of the log entry to do equality matching for.

        project: Name of the project to get logs from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A dict containing the grouped logs, with each key of the dict representing the
        version of the log key with equal values, and the value being a list of logs.
    """
    api_key = _validate_api_key(api_key)
    project = _get_and_maybe_create_project(project, api_key)
    return {
        k: get_logs(
            project,
            "{} == {}".format(key, '"' + v + '"' if isinstance(v, str) else v),
            api_key,
        )
        for k, v in get_groups(key, project, api_key).items()
    }


def get_logs_metric(
    metric: str,
    key: str,
    filter: Optional[str] = None,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Union[float, int, bool]:
    """
    Retrieve a set of log metrics across a project, after applying the filtering.

    Args:
        metric: The reduction metric to compute for the specified key. Supported are:
        sum, mean, var, std, min, max, median, mode.

        key: The key to compute the reduction statistic for.

        filter: The filtering to apply to the various log values, expressed as a string,
        for example:
        "(temperature > 0.5 and (len(system_msg) < 100 or 'no' in usr_response))"

        project: The id of the project to retrieve the logs for.

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
    project = _get_and_maybe_create_project(project, api_key)
    params = {"project": project, "filter_expr": filter}
    response = requests.get(
        BASE_URL + f"/logs/metric/{metric}/{key}",
        headers=headers,
        params=params,
    )
    response.raise_for_status()
    return response.json()


# if an active log is there, means the function is being called from within another traced function
# if no active log, create a new log
class trace:

    def __enter__(self):
        self.current_global_active_log_already_set = False
        current_active_log = current_global_active_log.get()
        if current_active_log is not None:
            self.current_global_active_log_already_set = True
        else:
            self.token = current_global_active_log.set(log())
            # print(current_global_active_log.get().id)

    def __exit__(self, *args, **kwargs):
        if not self.current_global_active_log_already_set:
            current_global_active_log.reset(self.token)

    def __call__(self, fn):
        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            with trace():
                result = await fn(*args, **kwargs)
                return result

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with trace():
                result = fn(*args, **kwargs)
                return result

        return async_wrapper if inspect.iscoroutinefunction(fn) else wrapper


class Context:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __enter__(self):
        self.token = current_global_active_log_kwargs.set(
            {**current_global_active_log_kwargs.get(), **self.kwargs},
        )
        self.nest_level_token = current_context_nest_level.set(
            current_context_nest_level.get() + 1,
        )

    def __exit__(self, *args, **kwargs):
        # print("Before clearing", current_global_active_log_kwargs.get())
        current_global_active_log_kwargs.reset(self.token)
        current_context_nest_level.reset(self.nest_level_token)
        if current_context_nest_level.get() == 0:
            current_logged_logs.set({})
