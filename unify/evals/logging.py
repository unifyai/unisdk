from __future__ import annotations

import inspect
import time
import uuid
import functools
import datetime
import json
from contextvars import ContextVar
from typing import Any, Dict, List, Optional, Union, Tuple

import requests
import unify
from unify import BASE_URL

from ..utils.helpers import _validate_api_key, _get_and_maybe_create_project

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

# span
current_span = ContextVar("current_span", default={})
running_time = ContextVar("running_time", default=0.0)


def _enclose_str(v):
    return json.dumps(v) if isinstance(v, str) else v


def _handle_special_types(
    kwargs: Dict[str, Any],
) -> Dict[str, Any]:
    new_kwargs = dict()
    for k, v in kwargs.items():
        if isinstance(v, unify.Dataset):
            v.upload()
            new_kwargs[k] = v.name
        elif callable(v):
            new_kwargs[k] = inspect.getsource(v)
        else:
            new_kwargs[k] = v
    return new_kwargs


def handle_multiple_logs(fn: callable):

    def wrapped(
        *args,
        logs: Optional[Union[int, Log, List[Union[int, Log]]]] = None,
        **kwargs,
    ):
        if logs is None and "logs" in fn.__code__.co_varnames:
            idx = fn.__code__.co_varnames.index("logs")
            if len(args) > idx:
                logs = args[idx]
                for i, val in enumerate(args[0:idx]):
                    kwargs[fn.__code__.co_varnames[i]] = val
                for i, val in enumerate(args[idx + 1 :]):
                    kwargs[fn.__code__.co_varnames[idx + i + 1]] = val
                args = ()
        if logs is None:
            current_active_log: Optional[Log] = current_global_active_log.get()
            if current_active_log is None:
                raise Exception(
                    "If logs is unspecified, then current_global_active_log must be.",
                )
            return fn(*args, logs=current_active_log.id, **kwargs)
        elif isinstance(logs, int):
            return fn(*args, logs=logs, **kwargs)
        elif isinstance(logs, Log):
            return fn(*args, logs=logs.id, **kwargs)
        elif isinstance(logs, list):
            if isinstance(logs[0], int):
                return unify.map(lambda lg: fn(*args, logs=lg, **kwargs), logs)
            elif isinstance(logs[0], Log):
                return unify.map(lambda lg: fn(*args, logs=lg.id, **kwargs), logs)
            else:
                raise Exception(
                    f"list must contain int or Log types, but found first entry "
                    f"{logs[0]} of type {type(logs[0])}",
                )
        else:
            raise Exception(
                f"logs argument must be of type int, Log, or list, but found "
                f"{logs} of type {type(logs)}",
            )

    return wrapped


# Projects #
# ---------#


def create_project(
    name: str,
    overwrite: bool = False,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Creates a logging project and adds this to your account. This project will have
    a set of logs associated with it.

    Args:
        name: A unique, user-defined name used when referencing the project.

        overwrite: Whether to overwrite an existing project if is already exists.

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
    if overwrite:
        if name in list_projects(api_key):
            delete_project(name, api_key=api_key)
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
    project = _get_and_maybe_create_project(project, api_key=api_key)
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
    project = _get_and_maybe_create_project(project, api_key=api_key)
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
    project = _get_and_maybe_create_project(project, api_key=api_key)
    response = requests.get(BASE_URL + f"/project/{project}/artifacts", headers=headers)
    response.raise_for_status()
    return response.json()


# Config #
# -------#


class Config:

    def __init__(
        self,
        **kwargs: Any,
    ):
        self._parameters = kwargs

    @property
    def parameters(self) -> Dict[str, Any]:
        return self._parameters

    def to_json(self):
        return {
            "parameters": self._parameters,
        }

    @staticmethod
    def from_json(state):
        assert "parameters" in state
        return Config(**state["parameters"])


# Logs #
# -----#


class Log:

    def __init__(
        self,
        id: int,
        timestamp: Optional[datetime] = None,
        api_key: Optional[str] = None,
        config: Config = None,
        **kwargs,
    ):
        self._id = id
        self._timestamp = timestamp
        self._entries = kwargs
        self._config = config
        self._api_key = _validate_api_key(api_key)

    # Properties

    @property
    def id(self) -> int:
        return self._id

    @property
    def timestamp(self) -> Optional[datetime]:
        return self._timestamp

    @property
    def entries(self) -> Dict[str, Any]:
        return self._entries

    @property
    def config(self) -> Config:
        return self._config

    # Dunders

    def __eq__(self, other: Union[dict, Log]) -> bool:
        if isinstance(other, dict):
            other = Log(other["id"], **other["entries"])
        return self._id == other._id

    def __len__(self):
        return len(self._entries)

    def __repr__(self) -> str:
        return f"Log(id={self._id})"

    # Public

    def download(self):
        self._entries = get_log_by_id(self._id, self._api_key)._entries

    def add_entries(self, **kwargs) -> None:
        add_log_entries(self._id, api_key=self._api_key, **kwargs)
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

    def delete_entries(
        self,
        keys_to_delete: List[str],
    ) -> None:
        for key in keys_to_delete:
            delete_log_entry(key, self._id, self._api_key)
            del self._entries[key]

    def delete(self) -> None:
        delete_log(self._id, self._api_key)

    def to_json(self):
        return {
            "id": self._id,
            "timestamp": self._timestamp,
            "entries": self._entries,
            "config": self._config.to_json(),
            "api_key": self._api_key,
        }

    @staticmethod
    def from_json(state):
        entries = state["entries"]
        del state["entries"]
        state = {**state, **entries}
        return Log(**state)


def log(
    project: Optional[str] = None,
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
    kwargs = {**kwargs, **current_global_active_log_kwargs.get()}
    kwargs = _handle_special_types(kwargs)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    if skip_duplicates:
        retrieved_logs = get_logs_by_value(project, **kwargs, api_key=api_key)
        if retrieved_logs:
            assert len(retrieved_logs) == 1, (
                f"When skip_duplicates == True, then it's expected that each log "
                f"entry is unique, but found {len(retrieved_logs)} entries with "
                f"config {kwargs}"
            )
            return retrieved_logs[0]
    body = {"project": project, "entries": kwargs}
    response = requests.post(BASE_URL + "/log", headers=headers, json=body)
    response.raise_for_status()
    created_log = Log(response.json(), api_key=api_key, **kwargs)
    if current_context_nest_level.get() > 0:
        current_logged_logs.set(
            {
                **current_logged_logs.get(),
                created_log.id: list(current_global_active_log_kwargs.get().keys()),
            },
        )
    return created_log


@handle_multiple_logs
def add_log_entries(
    logs: Optional[Union[int, Log, List[Union[int, Log]]]] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    """
    Add extra entries into an existing log.

    Args:
        logs: The log(s) to update with extra data. Looks for the current active log if
        no id is provided.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: The data to log into the console.

    Returns:
        A message indicating whether the log was successfully updated.
    """
    log_id = logs  # handle_multiple_logs decorator handles logs, returning a single id
    current_active_log: Optional[Log] = current_global_active_log.get()
    if current_active_log is None and log_id is None:
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
                if k not in current_logged_logs.get().get(log_id, {})
            },
        }
    kwargs = {**kwargs, **current_global_active_log_kwargs.get()}
    kwargs = _handle_special_types(kwargs)
    body = {"entries": kwargs}
    # ToDo: remove this once duplicates are prevented in the backend
    current_keys = get_log_by_id(
        log_id if log_id else current_active_log.id,
    ).entries.keys()
    assert not any(key in body["entries"] for key in current_keys), (
        "Duplicate keys detected, please use replace_log_entries or "
        "update_log_entries if you want to replace or modify an existing key."
    )
    # End ToDo
    response = requests.put(
        BASE_URL + f"/log/{log_id if log_id else current_active_log.id}",
        headers=headers,
        json=body,
    )
    response.raise_for_status()
    return response.json()


@handle_multiple_logs
def delete_log(
    logs: Optional[Union[int, Log, List[Union[int, Log]]]] = None,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Deletes logs from a project.

    Args:
        logs: log(s) to delete from a project.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A message indicating whether the logs were successfully deleted.
    """
    log_id = logs  # handle_multiple_logs decorator handles logs, returning a single id
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.delete(BASE_URL + f"/log/{log_id}", headers=headers)
    response.raise_for_status()
    return response.json()


@handle_multiple_logs
def delete_log_entry(
    entry: str,
    logs: Optional[Union[int, Log, List[Union[int, Log]]]] = None,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Deletes an entry from a log.

    Args:
        entry: Name of the entries to delete from a given log.

        logs: log(s) to delete entries from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A message indicating whether the log entries were successfully deleted.
    """
    log_id = logs  # handle_multiple_logs decorator handles logs, returning a single id
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    entry = entry.replace("/", "-")
    response = requests.delete(
        BASE_URL + f"/log/{log_id}/entry/{entry}",
        headers=headers,
    )
    response.raise_for_status()
    return response.json()


@handle_multiple_logs
def replace_log_entries(
    logs: Optional[Union[int, Log, List[Union[int, Log]]]] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    """
    Replaces existing entries in an existing log.

    Args:
        logs: The log(s) to replace fields for. Looks for the current active log if none
        specified.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: The data to update in the log.

    Returns:
        A message indicating whether the log was successfully updated.
    """
    log_id = logs  # handle_multiple_logs decorator handles logs, returning a single id
    api_key = _validate_api_key(api_key)
    for k, v in kwargs.items():
        delete_log_entry(k, log_id, api_key=api_key)
    return add_log_entries(log_id, api_key=api_key, **kwargs)


@handle_multiple_logs
def update_log_entries(
    fn: Union[callable, Dict[str, callable]],
    logs: Optional[Union[int, Log, List[Union[int, Log]]]] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    """
    Updates existing entries in an existing log.

    Args:
        fn: The function or set of functions to apply to each field in the log.

        logs: The log(s) to update fields for. Looks for the current active log if not
        provided.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: The data to update in the log.

    Returns:
        A message indicating whether the log was successfully updated.
    """
    log_id = logs  # handle_multiple_logs decorator handles logs, returning a single id
    data = get_log_by_id(log_id, api_key=api_key).entries
    replacements = dict()
    for k, v in kwargs.items():
        f = fn[k] if isinstance(fn, dict) else fn
        replacements[k] = f(data[k], v)
    return replace_log_entries(log_id, api_key=api_key, **replacements)


@handle_multiple_logs
def rename_log_entries(
    logs: Optional[Union[int, Log, List[Union[int, Log]]]] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    """
    Renames the set of log entries.

    Args:
        logs: The log(s) to update the field names for. Looks for the current active log
        if none are provided.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: The field names to update in the log, with keys as old names and values
        as new names.

    Returns:
        A message indicating whether the log field names were successfully updated.
    """
    log_id = logs  # handle_multiple_logs decorator handles logs, returning a single id
    api_key = _validate_api_key(api_key)
    data = get_log_by_id(log_id, api_key=api_key).entries
    for old_name in kwargs.keys():
        delete_log_entry(old_name, log_id, api_key=api_key)
    new_entries = {new_name: data[old_name] for old_name, new_name in kwargs.items()}
    return add_log_entries(log_id, api_key=api_key, **new_entries)


def get_logs(
    project: Optional[str] = None,
    filter: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[Log]:
    """
    Returns a list of filtered logs from a project.

    Args:
        project: Name of the project to get logs from.

        filter: Boolean string to filter logs, for example:
        "(temperature > 0.5 and (len(system_msg) < 100 or 'no' in usr_response))"

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        The list of logs for the project, after optionally applying filtering.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    project = _get_and_maybe_create_project(project, api_key=api_key)
    params = {
        "project": project,
        "filter_expr": filter,
    }
    response = requests.get(BASE_URL + "/logs", headers=headers, params=params)
    response.raise_for_status()
    return [
        Log(dct["id"], **dct["entries"], api_key=api_key) for dct in response.json()
    ]


def delete_logs(
    project: Optional[str] = None,
    filter: Optional[str] = None,
    api_key: Optional[str] = None,
):
    """
    Returns a list of filtered logs from a project.

    Args:
        project: Name of the project to delete logs from.

        filter: Boolean string to filter logs for deletion, for example:
        "(temperature > 0.5 and (len(system_msg) < 100 or 'no' in usr_response))"

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        The list of deleted logs for the project, after optionally applying filtering.
    """
    logs = get_logs(project, filter, api_key=api_key)
    for log in logs:
        log.delete()
    return logs


def get_logs_with_fields(
    *fields: str,
    mode: str = "all",
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[Log]:
    """
    Returns a list of logs which contain the specified fields, either the logs which
    contain all of them ("all") or the logs which contain any of the fields ("any").

    Args:
        fields: The fields to retrieve logs for.

        mode: The retrieval mode, either returning the logs with all of the fields or
        the logs with any of the fields.

        project: Name of the project to get logs from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A list of logs which contain the specified fields.
    """
    api_key = _validate_api_key(api_key)
    mode = {"any": "or", "all": "and"}[mode]
    filter_exp = f" {mode} ".join([f"exists({field})" for field in fields])
    return get_logs(project, filter=filter_exp, api_key=api_key)


def get_logs_without_fields(
    *fields: str,
    mode: str = "all",
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[Log]:
    """
    Returns a list of logs which do not contain the specified fields, either the logs
    which do not contain all of the fields ("all") or the logs which do not contain any
    of the fields ("any").

    Args:
        fields: The fields to not retrieve logs for.

        mode: The retrieval mode, either returning the logs with do not contain all of
        the fields or the logs which do not contain any of the fields.

        project: Name of the project to get logs from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A list of logs which do not contain the specified fields.
    """
    api_key = _validate_api_key(api_key)
    mode = {"any": "and", "all": "or"}[mode]
    filter_exp = f" {mode} ".join([f"(not exists({field}))" for field in fields])
    return get_logs(project, filter=filter_exp, api_key=api_key)


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

        Whether or not to include logs which contain identical key-value pairs to all
        kwargs passed which are present in the log, but

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
    project = _get_and_maybe_create_project(project, api_key=api_key)
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
    project = _get_and_maybe_create_project(project, api_key=api_key)
    return {
        k: get_logs(
            project,
            "{} == {}".format(key, '"' + v + '"' if isinstance(v, str) else v),
            api_key=api_key,
        )
        for k, v in get_groups(key, project, api_key=api_key).items()
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
    project = _get_and_maybe_create_project(project, api_key=api_key)
    params = {"project": project, "filter_expr": filter}
    response = requests.get(
        BASE_URL + f"/logs/metric/{metric}/{key}",
        headers=headers,
        params=params,
    )
    response.raise_for_status()
    return response.json()


def group_logs_by_config(logs: List[Log]) -> Dict:
    configs = list(dict.fromkeys([json.dumps(lg.config.parameters) for lg in logs]))
    ret_dict = dict()
    for conf in configs:
        ret_dict[conf] = [lg for lg in logs if json.dumps(lg.config.parameters) == conf]
    return ret_dict


# If an active log is there, means the function is being called from within another
# traced function.
# If no active log, create a new log
class trace:

    def __enter__(self):
        self.current_global_active_log_already_set = False
        current_active_log = current_global_active_log.get()
        if current_active_log is not None:
            self.current_global_active_log_already_set = True
        else:
            self.token = current_global_active_log.set(log())

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
        self.kwargs = _handle_special_types(kwargs)

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


def span(io=True):
    def wrapper(fn):
        def wrapped(*args, **kwargs):
            t1 = time.perf_counter()
            if not current_span.get():
                running_time.set(t1)
            inputs = None
            if io:
                signature = inspect.signature(fn)
                bound_args = signature.bind(*args, **kwargs)
                bound_args.apply_defaults()
                inputs = bound_args.arguments
            new_span = {
                "id": str(uuid.uuid4()),
                "parent_span_id": (
                    None if not current_span.get() else current_span.get()["id"]
                ),
                "span_name": fn.__name__,
                "exec_time": None,
                "offset": round(
                    0.0 if not current_span.get() else t1 - running_time.get(),
                    2,
                ),
                "inputs": inputs,
                "outputs": None,
                "errors": None,
                "child_spans": [],
            }
            token = current_span.set(new_span)
            result = None
            try:
                result = fn(*args, **kwargs)
                return result
            except Exception as e:
                new_span["errors"] = str(e)
                raise e
            finally:
                t2 = time.perf_counter()
                exec_time = t2 - t1
                current_span.get()["exec_time"] = round(exec_time, 2)
                current_span.get()["outputs"] = (
                    None if result is None or not io else result
                )
                if token.old_value is token.MISSING:
                    unify.log(trace=current_span.get(), skip_duplicates=False)
                    current_span.reset(token)
                else:
                    current_span.reset(token)
                    current_span.get()["child_spans"].append(new_span)

        async def async_wrapped(*args, **kwargs):
            t1 = time.perf_counter()
            if not current_span.get():
                running_time.set(t1)
            inputs = None
            if io:
                signature = inspect.signature(fn)
                bound_args = signature.bind(*args, **kwargs)
                bound_args.apply_defaults()
                inputs = bound_args.arguments
            new_span = {
                "id": str(uuid.uuid4()),
                "parent_span_id": (
                    None if not current_span.get() else current_span.get()["id"]
                ),
                "span_name": fn.__name__,
                "exec_time": None,
                "offset": round(
                    0.0 if not current_span.get() else t1 - running_time.get(),
                    2,
                ),
                "inputs": inputs,
                "outputs": None,
                "errors": None,
                "child_spans": [],
            }
            token = current_span.set(new_span)
            # capture the arguments here
            result = None
            try:
                result = await fn(*args, **kwargs)
                return result
            except Exception as e:
                new_span["errors"] = str(e)
                raise e
            finally:
                t2 = time.perf_counter()
                exec_time = t2 - t1
                current_span.get()["exec_time"] = round(exec_time, 2)
                current_span.get()["outputs"] = (
                    None if result is None or not io else result
                )
                if token.old_value is token.MISSING:
                    unify.log(trace=current_span.get(), skip_duplicates=False)
                    current_span.reset(token)
                else:
                    current_span.reset(token)
                    current_span.get()["child_spans"].append(new_span)

        return wrapped if not inspect.iscoroutinefunction(fn) else async_wrapped

    return wrapper
