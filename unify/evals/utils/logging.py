from __future__ import annotations
import inspect
from contextvars import ContextVar
from typing import Any, Dict, List, Optional, Union

import requests
import unify
from unify import BASE_URL
from ...utils.helpers import _validate_api_key, _get_and_maybe_create_project

# trace
current_global_active_log = ContextVar("current_global_active_log", default=None)

# Context
current_global_active_log_entries = ContextVar(
    "current_global_active_kwargs",
    default={},
)
current_logged_logs = ContextVar("current_logged_logs_ids", default={})
current_entries_nest_level = ContextVar("current_context_nest_level", default=0)

# span
current_span = ContextVar("current_span", default={})
running_time = ContextVar("running_time", default=0.0)


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


def _to_log_ids(
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
):
    if logs is None:
        current_active_log: Optional[unify.Log] = current_global_active_log.get()
        if current_active_log is None:
            raise Exception(
                "If logs is unspecified, then current_global_active_log must be.",
            )
        return [current_active_log.id]
    elif isinstance(logs, int):
        return [logs]
    elif isinstance(logs, unify.Log):
        return [logs.id]
    elif isinstance(logs, list):
        if isinstance(logs[0], int):
            return logs
        elif isinstance(logs[0], unify.Log):
            return [lg.id for lg in logs]
        else:
            raise Exception(
                f"list must contain int or unify.Log types, but found first entry "
                f"{logs[0]} of type {type(logs[0])}",
            )
    else:
        raise Exception(
            f"logs argument must be of type int, unify.Log, or list, but found "
            f"{logs} of type {type(logs)}",
        )


def log(
    project: Optional[str] = None,
    skip_duplicates: bool = True,
    api_key: Optional[str] = None,
    **kwargs,
) -> unify.Log:
    """
    Creates one or more logs associated to a project. unify.Logs are LLM-call-level data
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
    kwargs = {**kwargs, **current_global_active_log_entries.get()}
    kwargs = _handle_special_types(kwargs)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    if skip_duplicates:
        retrieved_logs = unify.get_logs_by_value(project, **kwargs, api_key=api_key)
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
    created_log = unify.Log(response.json(), api_key=api_key, **kwargs)
    if current_entries_nest_level.get() > 0:
        current_logged_logs.set(
            {
                **current_logged_logs.get(),
                created_log.id: list(current_global_active_log_entries.get().keys()),
            },
        )
    return created_log


def add_log_entries(
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
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
    log_ids = _to_log_ids(logs)
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    all_kwargs = list()
    if current_entries_nest_level.get() > 0:
        for log_id in log_ids:
            combined_kwargs = {
                **kwargs,
                **{
                    k: v
                    for k, v in current_global_active_log_entries.get().items()
                    if k not in current_logged_logs.get().get(log_id, {})
                },
            }
            all_kwargs.append(combined_kwargs)
        assert all(kw == all_kwargs[0] for kw in all_kwargs), (
            "All logs must share the same context if they're all "
            "being updated at the same time."
        )
        kwargs = all_kwargs[0]
    kwargs = _handle_special_types(kwargs)
    body = {"ids": log_ids, "entries": kwargs, "overwrite": False}
    response = requests.put(
        BASE_URL + f"/logs",
        headers=headers,
        json=body,
    )
    response.raise_for_status()
    return response.json()


def delete_logs(
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
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
    log_ids = _to_log_ids(logs)
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {"ids": log_ids}
    response = requests.delete(BASE_URL + f"/logs", headers=headers, json=body)
    response.raise_for_status()
    return response.json()


def delete_log_entries(
    entry: str,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
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
    log_ids = _to_log_ids(logs)
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {"ids": log_ids}
    entry = entry.replace("/", "-")
    response = requests.delete(
        BASE_URL + f"/logs/entry/{entry}",
        headers=headers,
        json=body,
    )
    response.raise_for_status()
    return response.json()


def get_logs(
    project: Optional[str] = None,
    filter: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[unify.Log]:
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
    params, logs = response.json().values()
    return [
        unify.Log(
            id=dct["id"],
            timestamp=dct["ts"],
            **dct["entries"],
            parameters={k: params[k][v] for k, v in dct["params"].items()},
            api_key=api_key,
        )
        for dct in logs
    ]


def get_log_by_id(id: int, api_key: Optional[str] = None) -> unify.Log:
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
    return unify.Log(id, **response.json()["entries"])


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
