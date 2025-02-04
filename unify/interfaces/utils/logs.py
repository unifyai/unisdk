from __future__ import annotations

import copy
import os
import inspect
import requests
import logging
from contextvars import ContextVar
from typing import Any, Dict, List, Optional, Union, Callable

import unify
from unify import BASE_URL
from ...utils._caching import (
    _get_cache,
    _write_to_cache,
    _get_caching,
    _get_caching_fname,
)
from ...utils.helpers import _validate_api_key, _get_and_maybe_create_project

# logging
USR_LOGGING = True

# log
ACTIVE_LOG = ContextVar("active_log", default=[])
LOGGED = ContextVar("logged", default={})

# context
CONTEXT = ContextVar("context", default="")

# entries
ACTIVE_ENTRIES = ContextVar(
    "active_entries",
    default={},
)
ENTRIES_NEST_LEVEL = ContextVar("entries_nest_level", default=0)

# params
ACTIVE_PARAMS = ContextVar(
    "active_params",
    default={},
)
PARAMS_NEST_LEVEL = ContextVar("params_nest_level", default=0)

# span
SPAN = ContextVar("span", default={})
RUNNING_TIME = ContextVar("running_time", default=0.0)


def _removes_unique_trace_values(kw: Dict[str, Any]) -> Dict[str, Any]:
    del kw["id"]
    del kw["exec_time"]
    if "parent_span_id" in kw:
        del kw["parent_span_id"]
    if "child_spans" in kw:
        kw["child_spans"] = [
            _removes_unique_trace_values(cs) for cs in kw["child_spans"]
        ]
    return kw


def _handle_cache(fn: Callable) -> Callable:
    def wrapped(*args, **kwargs):
        if not _get_caching():
            return fn(*args, **kwargs)
        kw_for_key = copy.deepcopy(kwargs)
        if fn.__name__ == "add_log_entries" and "trace" in kwargs:
            kw_for_key["trace"] = _removes_unique_trace_values(kw_for_key["trace"])
        combined_kw = {**{f"arg{i}": a for i, a in enumerate(args)}, **kw_for_key}
        ret = _get_cache(
            fn_name=fn.__name__,
            kw=combined_kw,
            filename=_get_caching_fname(),
        )
        if ret is not None:
            return ret
        ret = fn(*args, **kwargs)
        _write_to_cache(
            fn_name=fn.__name__,
            kw=combined_kw,
            response=ret,
            filename=_get_caching_fname(),
        )
        return ret

    return wrapped


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
        current_active_logs = ACTIVE_LOG.get()
        if not current_active_logs:
            raise Exception(
                "If logs is unspecified, then current_global_active_log must be.",
            )
        return [current_active_logs[-1].id]
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


def _to_logs(
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
):
    if logs is None:
        current_active_logs = ACTIVE_LOG.get()
        if not current_active_logs:
            raise Exception(
                "If logs is unspecified, then current_global_active_log must be.",
            )
        return [current_active_logs[-1]]
    elif isinstance(logs, int):
        return [unify.Log(id=logs)]
    elif isinstance(logs, unify.Log):
        return [logs]
    elif isinstance(logs, list):
        if isinstance(logs[0], int):
            return [unify.Log(id=lg) for lg in logs]
        elif isinstance(logs[0], unify.Log):
            return logs
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


def _apply_context(**data):
    context = CONTEXT.get()
    return {os.path.join(context, k): v for k, v in data.items()}


@_handle_cache
def log(
    *,
    project: Optional[str] = None,
    params: Dict[str, Any] = None,
    new: bool = False,
    overwrite: bool = False,
    mutable: Optional[Union[bool, Dict[str, bool]]] = True,
    api_key: Optional[str] = None,
    **entries,
) -> unify.Log:
    """
    Creates one or more logs associated to a project. unify.Logs are LLM-call-level data
    that might depend on other variables. This method returns the id of the new
    stored log.

    Args:
        project: Name of the project the stored logs will be associated to.

        params: Dictionary containing one or more key:value pairs that will be
        logged into the platform as params.

        new: Whether to create a new log if there is a currently active global lob.
        Defaults to False, in which case log will add to the existing log.

        overwrite: If adding to an existing log, dictates whether or not to overwrite
        fields with the same name.

        mutable: Either a boolean to apply uniform mutability for all fields, or a dictionary mapping field names to booleans for per-field control. Defaults to True.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        entries: Dictionary containing one or more key:value pairs that will be logged
        into the platform as entries.

    Returns:
        The unique id of newly created log.
    """
    api_key = _validate_api_key(api_key)
    if not new and ACTIVE_LOG.get():
        _add_to_log(
            mode="entries",
            overwrite=overwrite,
            mutable=mutable,
            api_key=api_key,
            **entries,
        )
        _add_to_log(
            mode="params",
            overwrite=overwrite,
            mutable=mutable,
            api_key=api_key,
            **(params if params is not None else {}),
        )
        if USR_LOGGING:
            logging.info(f"Updated Log({ACTIVE_LOG.get().id})")
        return ACTIVE_LOG.get()[-1]
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    params = _apply_context(**(params if params else {}))
    entries = _apply_context(**entries)
    params = {**params, **ACTIVE_PARAMS.get()}
    params = _handle_special_types(params)
    entries = {**entries, **ACTIVE_ENTRIES.get()}
    entries = _handle_special_types(entries)
    if mutable is not None:
        if isinstance(mutable, dict):
            for field, mut in mutable.items():
                if field in params:
                    params.setdefault("explicit_types", {})[field] = {"mutable": mut}
                if field in entries:
                    entries.setdefault("explicit_types", {})[field] = {"mutable": mut}
        elif isinstance(mutable, bool):
            for k in list(params.keys()):
                if k != "explicit_types":
                    params.setdefault("explicit_types", {})[k] = {"mutable": mutable}
            for k in list(entries.keys()):
                if k != "explicit_types":
                    entries.setdefault("explicit_types", {})[k] = {"mutable": mutable}
    project = _get_and_maybe_create_project(project, api_key=api_key)
    body = {"project": project, "params": params, "entries": entries}
    response = requests.post(BASE_URL + "/logs", headers=headers, json=body)
    response.raise_for_status()
    created_log = unify.Log(
        id=response.json()[0],
        api_key=api_key,
        **entries,
        params=params,
    )
    if PARAMS_NEST_LEVEL.get() > 0 or ENTRIES_NEST_LEVEL.get() > 0:
        LOGGED.set(
            {
                **LOGGED.get(),
                created_log.id: list(params.keys()) + list(entries.keys()),
            },
        )
    if USR_LOGGING:
        logging.info(f"Created Log({created_log.id})")
    return created_log


@_handle_cache
def _add_to_log(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    mode: str = None,
    overwrite: bool = False,
    mutable: Optional[Union[bool, Dict[str, bool]]] = True,
    api_key: Optional[str] = None,
    **data,
) -> Dict[str, str]:
    assert mode in (
        "params",
        "entries",
    ), "mode must be one of 'params', 'entries'"
    data = _apply_context(**data)
    nest_level = {
        "params": PARAMS_NEST_LEVEL,
        "entries": ENTRIES_NEST_LEVEL,
    }[mode]
    active = {
        "params": ACTIVE_PARAMS,
        "entries": ACTIVE_ENTRIES,
    }[mode]
    log_ids = _to_log_ids(logs)
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    all_kwargs = list()
    if nest_level.get() > 0:
        for log_id in log_ids:
            combined_kwargs = {
                **data,
                **{
                    k: v
                    for k, v in active.get().items()
                    if k not in LOGGED.get().get(log_id, {})
                },
            }
            all_kwargs.append(combined_kwargs)
        assert all(kw == all_kwargs[0] for kw in all_kwargs), (
            "All logs must share the same context if they're all "
            "being updated at the same time."
        )
        data = all_kwargs[0]
    data = _handle_special_types(data)
    if mutable is not None:
        if isinstance(mutable, dict):
            for field, mut in mutable.items():
                data.setdefault("explicit_types", {})[field] = {"mutable": mut}
        elif isinstance(mutable, bool):
            for k in list(data.keys()):
                if k != "explicit_types":
                    data.setdefault("explicit_types", {})[k] = {"mutable": mutable}
    body = {
        "ids": log_ids,
        mode: data,
        "overwrite": overwrite,
    }
    response = requests.put(
        BASE_URL + f"/logs",
        headers=headers,
        json=body,
    )
    response.raise_for_status()
    if nest_level.get() > 0:
        logged = LOGGED.get()
        new_logged = dict()
        for log_id in log_ids:
            if log_id in logged:
                new_logged[log_id] = logged[log_id] + list(data.keys())
            else:
                new_logged[log_id] = list(data.keys())
        LOGGED.set(
            {
                **logged,
                **new_logged,
            },
        )
    return response.json()


@_handle_cache
def add_log_params(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    mutable: Optional[Union[bool, Dict[str, bool]]] = True,
    api_key: Optional[str] = None,
    **params,
) -> Dict[str, str]:
    """
    Add extra entries into an existing log.

    Args:
        logs: The log(s) to update with extra data. Looks for the current active log if
        no id is provided.

        mutable: Either a boolean to apply uniform mutability for all parameters, or a dictionary mapping parameter names to booleans for per-field control.
        Defaults to True.
        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        params: Dictionary containing one or more key:value pairs that will be
        logged into the platform as params.

    Returns:
        A message indicating whether the logs were successfully updated.
    """
    ret = _add_to_log(
        logs=logs,
        mode="params",
        mutable=mutable,
        api_key=api_key,
        **params,
    )
    if USR_LOGGING:
        logging.info(
            f"Added Params {', '.join(list(params.keys()))} "
            f"to Logs({', '.join(_to_log_ids(logs))})",
        )
    return ret


@_handle_cache
def add_log_entries(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    overwrite: bool = False,
    mutable: Optional[Union[bool, Dict[str, bool]]] = True,
    api_key: Optional[str] = None,
    **entries,
) -> Dict[str, str]:
    """
    Add extra entries into an existing log.

    Args:
        logs: The log(s) to update with extra data. Looks for the current active log if
        no id is provided.

        overwrite: Whether or not to overwrite an entry pre-existing with the same name.

        mutable: Either a boolean to apply uniform mutability for all entries, or a dictionary mapping entry names to booleans for per-field control.
        Defaults to True.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        entries: Dictionary containing one or more key:value pairs that will be logged
        into the platform as entries.

    Returns:
        A message indicating whether the logs were successfully updated.
    """
    ret = _add_to_log(
        logs=logs,
        mode="entries",
        overwrite=overwrite,
        mutable=mutable,
        api_key=api_key,
        **entries,
    )
    if USR_LOGGING:
        logging.info(
            f"Added Entries {', '.join(list(entries.keys()))} "
            f"to Logs({', '.join(_to_log_ids(logs))})",
        )
    return ret


@_handle_cache
def delete_logs(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Deletes logs from a project.

    Args:
        logs: log(s) to delete from a project.

        project: Name of the project to delete logs from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A message indicating whether the logs were successfully deleted.
    """
    if logs is None:
        logs = get_logs(project=project, api_key=api_key)
        if not logs:
            return {"message": "No logs to delete"}
    log_ids = _to_log_ids(logs)
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {"ids_and_fields": [(log_ids, None)]}
    response = requests.delete(BASE_URL + f"/logs", headers=headers, json=body)
    response.raise_for_status()
    if USR_LOGGING:
        logging.info(f"Deleted Logs({', '.join(log_ids)})")
    return response.json()


@_handle_cache
def delete_log_fields(
    *,
    field: str,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Deletes an entry from a log.

    Args:
        field: Name of the field to delete from the given logs.

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
    body = {"ids_and_fields": [(log_ids, field)]}
    response = requests.delete(
        BASE_URL + f"/logs",
        headers=headers,
        json=body,
    )
    response.raise_for_status()
    if USR_LOGGING:
        logging.info(f"Deleted Field `{field}` from Logs({', '.join(log_ids)})")
    return response.json()


# noinspection PyShadowingBuiltins
def get_logs(
    *,
    project: Optional[str] = None,
    filter: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
    api_key: Optional[str] = None,
) -> List[unify.Log]:
    """
    Returns a list of filtered logs from a project.

    Args:
        project: Name of the project to get logs from.

        filter: Boolean string to filter logs, for example:
        "(temperature > 0.5 and (len(system_msg) < 100 or 'no' in usr_response))"

        limit: The maximum number of logs to return. Default is None (unlimited).

        offset: The starting index of the logs to return. Default is 0.

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
        "limit": limit,
        "offset": offset,
    }
    response = requests.get(BASE_URL + "/logs", headers=headers, params=params)
    response.raise_for_status()
    params, logs, _ = response.json().values()
    return [
        unify.Log(
            id=dct["id"],
            ts=dct["ts"],
            **dct["entries"],
            params={
                param_name: (param_ver, params[param_name][param_ver])
                for param_name, param_ver in dct["params"].items()
            },
            api_key=api_key,
        )
        for dct in logs
    ]


# noinspection PyShadowingBuiltins
def get_log_by_id(
    id: int,
    project: Optional[str] = None,
    *,
    api_key: Optional[str] = None,
) -> unify.Log:
    """
    Returns the log associated with a given id.

    Args:
        id: IDs of the logs to fetch.

        project: Name of the project to get logs from.

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
    project = _get_and_maybe_create_project(project, api_key=api_key)
    response = requests.get(
        BASE_URL + "/logs",
        params={"project": project, "from_ids": [id]},
        headers=headers,
    )
    response.raise_for_status()
    params, lgs, count = response.json().values()
    if len(lgs) == 0:
        raise Exception(f"Log with id {id} does not exist")
    lg = lgs[0]
    return unify.Log(
        id=lg["id"],
        ts=lg["ts"],
        **lg["entries"],
        params={k: params[k][v] for k, v in lg["params"].items()},
        api_key=api_key,
    )


# noinspection PyShadowingBuiltins
def get_logs_metric(
    *,
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
    params = {"project": project, "filter_expr": filter, "key": key}
    response = requests.get(
        BASE_URL + f"/logs/metric/{metric}",
        headers=headers,
        params=params,
    )
    response.raise_for_status()
    return response.json()


def get_groups(
    *,
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


# User Logging #
# -------------#


def set_user_logging(value: bool):
    global USR_LOGGING
    USR_LOGGING = value
