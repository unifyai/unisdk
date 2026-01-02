from __future__ import annotations

import inspect
import json
import logging
import os
import sys
from contextvars import ContextVar
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import unify
from tqdm import tqdm
from unify import BASE_URL
from unify.utils import http
from unify.utils.helpers import flexible_deepcopy

from ...utils._caching import _get_cache, _write_to_cache, is_caching_enabled
from ...utils.helpers import (
    _create_request_header,
    _get_and_maybe_create_project,
    _validate_api_key,
)
from .async_logger import AsyncLoggerManager

logger = logging.getLogger(__name__)

# logging configuration
USR_LOGGING = True
ASYNC_LOGGING = False  # Flag to enable/disable async logging
ASYNC_BATCH_SIZE = 100  # Default batch size for async logging
ASYNC_FLUSH_INTERVAL = 5.0  # Default flush interval in secondss
ASYNC_MAX_QUEUE_SIZE = 10000  # Default maximum queue size

_async_logger: Optional[AsyncLoggerManager] = None

# log
ACTIVE_LOG = ContextVar("active_log", default=[])
LOGGED = ContextVar("logged", default={})

# context
CONTEXT_READ = ContextVar("context_read", default="")
CONTEXT_WRITE = ContextVar("context_write", default="")
CONTEXT_MODE = ContextVar("context_mode", default="both")

# context function
MODE = None
MODE_TOKEN = None
CONTEXT_READ_TOKEN = None
CONTEXT_WRITE_TOKEN = None

# column context
COLUMN_CONTEXT_READ = ContextVar("column_context_read", default="")
COLUMN_CONTEXT_WRITE = ContextVar("column_context_write", default="")
COLUMN_CONTEXT_MODE = ContextVar("column_context_mode", default="both")

# entries
ACTIVE_ENTRIES_WRITE = ContextVar(
    "active_entries_write",
    default={},
)
ACTIVE_ENTRIES_READ = ContextVar(
    "active_entries_read",
    default={},
)
ACTIVE_ENTRIES_MODE = ContextVar("active_entries_mode", default="both")
ENTRIES_NEST_LEVEL = ContextVar("entries_nest_level", default=0)

# chunking
CHUNK_LIMIT = 5000000


def initialize_async_logger(
    queue_size: Optional[int] = 10000,
    api_key: Optional[str] = None,
) -> None:
    """
    Initialize the async logger with the specified configuration.

    Args:
        queue_size: Maximum number of log events to store in the queue, defaults to 10000.
        if maximum queue size is exceeded, calls to unify.log will block until space is available.

        api_key: API key for authentication
    """
    global _async_logger, ASYNC_LOGGING

    if _async_logger is not None:
        return
    api_key = _validate_api_key(api_key)
    _async_logger = AsyncLoggerManager(
        name="default",
        base_url=BASE_URL,
        api_key=api_key,
        max_queue_size=queue_size,
    )
    ASYNC_LOGGING = True


def shutdown_async_logger(immediate=False) -> None:
    """
    Gracefully shutdown the async logger, ensuring all pending logs are flushed.
    """
    global _async_logger, ASYNC_LOGGING

    if _async_logger is not None:
        _async_logger.stop_sync(immediate=immediate)
        _async_logger = None
        ASYNC_LOGGING = False


def _apply_row_ids_and_non_unique_auto_count_vals(
    row_ids_data: Optional[Dict[str, Any]],
    auto_counting_data: Optional[Dict[str, List[Any]]],
    entries: List[Dict[str, Any]],
) -> None:
    """
    Apply unique row_ids and non-unique auto_counting values from server response to entries.

    Behavior:
    - Apply row_ids (unique auto-incrementing keys) first, using the standardized format
      {'names': List[str], 'ids': List[List[int]]}.
    - Then, apply auto_counting key/value pairs ONLY for keys not already included in
      row_ids.names. This ensures unique keys come from row_ids while additional
      non-unique counters (e.g., independent counters) are also populated.

    Args:
        row_ids_data: The row_ids data from server response.
        auto_counting_data: The auto_counting data from server response, mapping key -> List[Any].
        entries: List of entry dictionaries to update.
    """
    # 1) Apply row_ids (unique keys)
    row_id_names: List[str] = []
    if row_ids_data:
        names = row_ids_data.get("names")
        ids = row_ids_data.get("ids")

        if names and ids:
            # Ensure names is always a list for consistent processing
            if not isinstance(names, list):
                names = [names]
            row_id_names = names

            # Apply IDs to entries
            for entry, id_values in zip(entries, ids):
                if id_values is not None:
                    # Handle both nested ID format (list of lists) and flat format (list of values)
                    if isinstance(id_values, list) and len(names) > 1:
                        # Nested format: zip names with id_values
                        id_dict = dict(zip(names, id_values))
                        entry.update(id_dict)
                    else:
                        # Single ID format: use first name with the id_value
                        if isinstance(id_values, list) and len(id_values) == 1:
                            entry[names[0]] = id_values[0]
                        else:
                            entry[names[0]] = id_values

    # 2) Apply auto_counting (non-unique and any additional counters)
    if auto_counting_data:
        # Treat row_id_names as a set for fast membership checks
        row_id_names_set = set(row_id_names)
        # For each auto_counting key, if not a row_id key, propagate values into entries
        for key, values in auto_counting_data.items():
            if key in row_id_names_set:
                # Skip keys already applied via row_ids
                continue
            if not isinstance(values, list):
                # Defensive: backend guarantees list, but guard just in case
                continue
            for idx, entry in enumerate(entries):
                if idx < len(values):
                    entry[key] = values[idx]


def _handle_cache(fn: Callable) -> Callable:
    def wrapped(*args, **kwargs):
        if not is_caching_enabled():
            return fn(*args, **kwargs)
        kw_for_key = flexible_deepcopy(kwargs)
        combined_kw = {**{f"arg{i}": a for i, a in enumerate(args)}, **kw_for_key}
        ret = _get_cache(
            fn_name=fn.__name__,
            kw=combined_kw,
        )
        if ret is not None:
            return ret
        ret = fn(*args, **kwargs)
        _write_to_cache(
            fn_name=fn.__name__,
            kw=combined_kw,
            response=ret,
        )
        return ret

    return wrapped


def _handle_special_types(
    kwargs: Dict[str, Any],
) -> Dict[str, Any]:
    new_kwargs = dict()
    for k, v in kwargs.items():
        if callable(v):
            new_kwargs[k] = inspect.getsource(v)
        else:
            new_kwargs[k] = v
    return new_kwargs


def _to_log_ids(
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
):
    def resolve_log_id(log):
        if isinstance(log, unify.Log):
            if log.id is None and hasattr(log, "_future"):
                try:
                    # Wait (with timeout) for the future to resolve
                    log._id = log._future.result(timeout=5)
                except Exception as e:
                    raise Exception(f"Failed to resolve log id: {e}")
            return log.id
        return log

    if logs is None:
        current_active_logs = ACTIVE_LOG.get()
        if not current_active_logs:
            raise Exception(
                "If logs is unspecified, then current_global_active_log must be.",
            )
        return [resolve_log_id(current_active_logs[-1])]
    elif isinstance(logs, int):
        return [logs]
    elif isinstance(logs, unify.Log):
        return [resolve_log_id(logs)]
    elif isinstance(logs, list):
        if not logs:
            return logs
        elif isinstance(logs[0], int):
            return logs
        elif isinstance(logs[0], unify.Log):
            return [resolve_log_id(lg) for lg in logs]
        else:
            raise Exception(
                f"list must contain int or unify.Log types, but found first entry {logs[0]} of type {type(logs[0])}",
            )
    raise Exception(
        f"logs argument must be of type int, unify.Log, or list, but found {logs} of type {type(logs)}",
    )


def _apply_col_context(**data):
    if COLUMN_CONTEXT_MODE.get() == "both":
        assert COLUMN_CONTEXT_WRITE.get() == COLUMN_CONTEXT_READ.get()
        col_context = COLUMN_CONTEXT_WRITE.get()
    elif COLUMN_CONTEXT_MODE.get() == "write":
        col_context = COLUMN_CONTEXT_WRITE.get()
    elif COLUMN_CONTEXT_MODE.get() == "read":
        col_context = COLUMN_CONTEXT_READ.get()
    return {os.path.join(col_context, k): v for k, v in data.items()}


def _handle_context(context: Optional[Union[str, Dict[str, str]]] = None):
    if context is None:
        return {"name": CONTEXT_WRITE.get()}
    if isinstance(context, str):
        return {"name": context}
    else:
        return context


def _handle_mutability(
    mutable: Optional[Union[bool, Dict[str, bool]]],
    data: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None,
):
    if mutable is None or data is None:
        return data

    if isinstance(data, list):
        single_item = False
        new_data = flexible_deepcopy(data, on_fail="shallow")
    else:
        single_item = True
        new_data = [flexible_deepcopy(data, on_fail="shallow")]
    if isinstance(mutable, dict):
        for item in new_data:
            et = item.get("explicit_types")
            if not isinstance(et, dict):
                et = {}
                item["explicit_types"] = et
            for field, mut in mutable.items():
                if field in item:
                    existing = (
                        et.get(field, {}) if isinstance(et.get(field, {}), dict) else {}
                    )
                    existing = {**existing, "mutable": mut}
                    et[field] = existing
    elif isinstance(mutable, bool):
        for item in new_data:
            et = item.get("explicit_types")
            if not isinstance(et, dict):
                et = {}
                item["explicit_types"] = et
            for k in list(item.keys()):
                if k == "explicit_types":
                    continue
                existing = et.get(k, {}) if isinstance(et.get(k, {}), dict) else {}
                existing = {**existing, "mutable": mutable}
                et[k] = existing
    if single_item:
        return new_data[0]
    return new_data


def _json_chunker(big_dict, chunk_size=1024 * 1024):
    json_string = json.dumps(big_dict)
    total_bytes = len(json_string)
    pbar = tqdm(total=total_bytes, unit="B", unit_scale=True, desc="Uploading JSON")
    start = 0
    while start < total_bytes:
        end = min(start + chunk_size, total_bytes)
        chunk = json_string[start:end]
        yield chunk
        pbar.update(len(chunk))
        start = end
    pbar.close()


def log(
    *,
    project: Optional[str] = None,
    context: Optional[str] = None,
    new: bool = False,
    overwrite: bool = False,
    mutable: Optional[Union[bool, Dict[str, bool]]] = True,
    api_key: Optional[str] = None,
    **entries,
) -> unify.Log:
    """
    Creates one or more logs associated to a project. unify.Logs are LLM-call-level data
    that might depend on other variables.

    Args:
        project: Name of the project the stored logs will be associated to.

        context: Context for the logs.

        new: Whether to create a new log if there is a currently active global log.
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
    global ASYNC_LOGGING
    api_key = _validate_api_key(api_key)
    context = _handle_context(context)
    if not new and ACTIVE_LOG.get():
        _add_to_log(
            context=context,
            overwrite=overwrite,
            mutable=mutable,
            api_key=api_key,
            **entries,
        )
        log = ACTIVE_LOG.get()[-1]
        if USR_LOGGING:
            logger.info(f"Updated Log({log.id})")
        return log
    # Process entries
    entries = _apply_col_context(**entries)
    entries = {**entries, **ACTIVE_ENTRIES_WRITE.get()}
    entries = _handle_special_types(entries)
    entries = _handle_mutability(mutable, entries)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    if ASYNC_LOGGING and _async_logger is not None:
        # Use async logging: enqueue a create event and capture the Future.
        log_future = _async_logger.log_create(
            project=project,
            context=context,
            entries=entries,
        )
        created_log = unify.Log(
            id=None,  # Placeholder; will be updated when the Future resolves.
            _future=log_future,
            api_key=api_key,
            **entries,
            context=context,
        )
    else:
        # Use synchronous logging
        created_log = _sync_log(
            project=project,
            context=context,
            entries=entries,
            api_key=api_key,
        )

    created_log.entries.pop("explicit_types", None)

    if ENTRIES_NEST_LEVEL.get() > 0:
        LOGGED.set(
            {
                **LOGGED.get(),
                created_log.id: list(entries.keys()),
            },
        )
    if USR_LOGGING:
        logger.info(f"Created Log({created_log.id})")
    return created_log


def _sync_log(
    project: str,
    context: Optional[str],
    entries: Dict[str, Any],
    api_key: str,
) -> unify.Log:
    """
    Synchronously create a log entry using direct HTTP request.

    This is a helper function used when async logging is disabled or unavailable.
    """
    headers = _create_request_header(api_key)

    body = {
        "project": project,
        "context": context,
        "entries": entries,
    }
    response = http.post(BASE_URL + "/logs", headers=headers, json=body)
    resp_json = response.json()

    # Apply row_ids and non-unique auto_counting values to entries
    _apply_row_ids_and_non_unique_auto_count_vals(
        resp_json.get("row_ids"),
        resp_json.get("auto_counting"),
        [entries],
    )

    return unify.Log(
        id=resp_json["log_event_ids"][0],
        api_key=api_key,
        **entries,
        context=context,
    )


def _create_log(dct, context, api_key, context_entries=None):
    if context_entries is None:
        context_entries = {}
    return unify.Log(
        id=dct["id"],
        ts=dct["ts"],
        **dct["entries"],
        **dct["derived_entries"],
        **context_entries,
        context=context,
        api_key=api_key,
    )


def _create_log_groups_nested(
    context,
    api_key,
    node,
    context_entries,
    prev_key=None,
):
    if isinstance(node, dict) and "group" not in node:
        ret = unify.LogGroup(list(node.keys())[0])
        ret.value = _create_log_groups_nested(
            context,
            api_key,
            node[ret.field],
            context_entries,
            ret.field,
        )
        return ret
    else:
        if isinstance(node["group"][0]["value"], list):
            ret = {}
            for n in node["group"]:
                context_entries[prev_key] = n["key"]
                ret[n["key"]] = [
                    _create_log(
                        item,
                        context,
                        api_key,
                        context_entries,
                    )
                    for item in n["value"]
                ]
            return ret
        else:
            ret = {}
            for n in node["group"]:
                context_entries[prev_key] = n["key"]
                ret[n["key"]] = _create_log_groups_nested(
                    context,
                    api_key,
                    n["value"],
                    context_entries,
                    n["key"],
                )
            return ret


def _create_log_groups_not_nested(logs, groups, context, api_key):
    logs_mapping = {}
    for dct in logs:
        logs_mapping[dct["id"]] = _create_log(dct, context, api_key)

    ret = []
    for group_key, group_value in groups.items():
        if isinstance(group_value, dict):
            val = {}
            for k, v in group_value.items():
                if isinstance(v, list):
                    val[k] = [logs_mapping[log_id] for log_id in v]
            ret.append(unify.LogGroup(group_key, val))
    return ret


def create_logs(
    *,
    project: Optional[str] = None,
    context: Optional[str] = None,
    entries: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None,
    mutable: Optional[Union[bool, Dict[str, bool]]] = True,
    batched: Optional[bool] = None,
    api_key: Optional[str] = None,
) -> List[int]:
    """
    Creates one or more logs associated to a project.

    Args:
        project: Name of the project the stored logs will be associated to.

        context: Context for the logs.

        entries: List of dictionaries with the entries to be logged. For contexts with
        nested unique IDs, parent ID values can be passed directly in the entries
        dictionaries. For example, if a context has unique IDs `["run_id", "step_id"]`,
        you can pass `{"run_id": 0, "data": "value"}` in entries to generate the next
        `step_id` for that particular run. The leftmost N-1 unique columns can be
        supplied as normal entry keys, and the rightmost column is always auto-incremented.

        mutable: Either a boolean to apply uniform mutability for all fields, or a dictionary mapping field names to booleans for per-field control. Defaults to True.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A list of the created logs.
    """
    api_key = _validate_api_key(api_key)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = _handle_context(context)
    headers = _create_request_header(api_key)
    entries = _handle_mutability(mutable, entries)
    if entries is None:
        entries = []
    body = {
        "project": project,
        "context": context,
        "entries": entries,
    }
    body_size = sys.getsizeof(json.dumps(body))
    if batched is None:
        batched = body_size < CHUNK_LIMIT
    if batched:
        if body_size < CHUNK_LIMIT:
            response = http.post(BASE_URL + "/logs", headers=headers, json=body)
        else:
            response = http.post(
                BASE_URL + "/logs",
                headers=headers,
                data=_json_chunker(body),
            )
        resp_json = response.json()

        # Apply row_ids and non-unique auto_counting values to entries
        _apply_row_ids_and_non_unique_auto_count_vals(
            resp_json.get("row_ids"),
            resp_json.get("auto_counting"),
            entries,
        )

        return [
            unify.Log(
                project=project,
                context=context["name"] if isinstance(context, dict) else context,
                **{k: v for k, v in e.items() if k != "explicit_types"},
                id=i,
            )
            for e, i in zip(entries, resp_json["log_event_ids"])
        ]

    # Fallback for non-batched (iterative) logging
    pbar = tqdm(total=len(entries), unit="logs", desc="Creating Logs")
    try:
        unify.initialize_async_logger()
        _async_logger.register_callback(lambda: pbar.update(1))
        ret = []

        for e in entries:
            ret.append(
                log(
                    project=project,
                    context=context,
                    new=True,
                    mutable=mutable,
                    api_key=api_key,
                    **e,
                ),
            )
    finally:
        unify.shutdown_async_logger()
        pbar.close()
    return ret


def _add_to_log(
    *,
    context: Optional[str] = None,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    overwrite: bool = False,
    mutable: Optional[Union[bool, Dict[str, bool]]] = True,
    api_key: Optional[str] = None,
    **data,
) -> Dict[str, str]:
    data = _apply_col_context(**data)
    api_key = _validate_api_key(api_key)
    context = _handle_context(context)
    data = _handle_special_types(data)
    data = _handle_mutability(mutable, data)
    if ASYNC_LOGGING and _async_logger is not None:
        # For simplicity, assume logs is a single unify.Log.
        if logs is None:
            log_obj = ACTIVE_LOG.get()[-1]
        elif isinstance(logs, unify.Log):
            log_obj = logs
        elif isinstance(logs, list) and logs and isinstance(logs[0], unify.Log):
            log_obj = logs[0]
        else:
            # If not a Log, resolve synchronously.
            log_id = _to_log_ids(logs)[0]
            lf = _async_logger._loop.create_future()
            lf.set_result(log_id)
            log_obj = unify.Log(id=log_id, _future=lf, api_key=api_key)
        # Prepare the future to pass (if the log is still pending, use its _future)
        if hasattr(log_obj, "_future") and log_obj._future is not None:
            lf = log_obj._future
        else:
            lf = _async_logger._loop.create_future()
            lf.set_result(log_obj.id)
        _async_logger.log_update(
            project=_get_and_maybe_create_project(None, api_key=api_key),
            context=context,
            future=lf,
            overwrite=overwrite,
            data=data,
        )
        return {"detail": "Update queued asynchronously"}
    else:
        # Fallback to synchronous update if async logging isn’t enabled.
        log_ids = _to_log_ids(logs)
        headers = _create_request_header(api_key)
        all_kwargs = []
        if ENTRIES_NEST_LEVEL.get() > 0:
            for log_id in log_ids:
                combined_kwargs = {
                    **data,
                    **{
                        k: v
                        for k, v in ACTIVE_ENTRIES_WRITE.get().items()
                        if k not in LOGGED.get().get(log_id, {})
                    },
                }
                all_kwargs.append(combined_kwargs)
            assert all(
                kw == all_kwargs[0] for kw in all_kwargs
            ), "All logs must share the same context if they're all being updated at the same time."
            data = all_kwargs[0]
        body = {
            "logs": log_ids,
            "entries": data,
            "overwrite": overwrite,
            "context": context,
        }
        response = http.put(BASE_URL + "/logs", headers=headers, json=body)
        if ENTRIES_NEST_LEVEL.get() > 0:
            logged = LOGGED.get()
            new_logged = {}
            for log_id in log_ids:
                if log_id in logged:
                    new_logged[log_id] = logged[log_id] + list(data.keys())
                else:
                    new_logged[log_id] = list(data.keys())
            LOGGED.set({**logged, **new_logged})
        return response.json()


def add_log_entries(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    overwrite: bool = False,
    mutable: Optional[Union[bool, Dict[str, bool]]] = True,
    api_key: Optional[str] = None,
    context: Optional[str] = None,
    **entries,
) -> Dict[str, str]:
    """
    Add extra entries into an existing log.

    Args:
        logs: The log(s) to update with extra entries. Looks for the current active log if
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
        overwrite=overwrite,
        mutable=mutable,
        api_key=api_key,
        context=context,
        **entries,
    )
    if USR_LOGGING:
        logger.info(
            f"Added Entries {', '.join(list(entries.keys()))} "
            f"to Logs({', '.join([str(i) for i in _to_log_ids(logs)])})",
        )
    return ret


def update_logs(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    context: Optional[Union[str, List[str]]] = None,
    entries: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
    overwrite: bool = False,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Updates existing logs.
    """
    if not logs and not entries:
        return {"detail": "No logs to update."}
    headers = _create_request_header(api_key)
    log_ids = _to_log_ids(logs)
    body = {
        "logs": log_ids,
        "context": context,
        "overwrite": overwrite,
    }
    if entries is not None:
        body["entries"] = entries
    response = http.put(BASE_URL + "/logs", headers=headers, json=body)
    return response.json()


def delete_logs(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    project: Optional[str] = None,
    context: Optional[str] = None,
    delete_empty_logs: bool = False,
    source_type: str = "all",
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Deletes logs from a project.

    Args:
        logs: log(s) to delete from a project.

        project: Name of the project to delete logs from.

        context: Context of the logs to delete. Logs will be removed from that context instead of being entirely deleted,
        unless it is the last context associated with the log.

        delete_empty_logs: Whether to delete logs that become empty after deleting the specified fields.

        source_type: Type of logs to delete. Can be "all", "derived", or "base".

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A message indicating whether the logs were successfully deleted.
    """
    if logs is None:
        logs = get_logs(project=project, context=context, api_key=api_key)
        if not logs:
            return {"message": "No logs to delete"}
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = context if context else CONTEXT_READ.get()
    log_ids = _to_log_ids(logs)
    headers = _create_request_header(api_key)
    body = {
        "project": project,
        "context": context,
        "ids_and_fields": [(log_ids, None)],
        "source_type": source_type,
    }
    params = {"delete_empty_logs": delete_empty_logs}
    response = http.delete(
        BASE_URL + "/logs",
        headers=headers,
        params=params,
        json=body,
    )
    if USR_LOGGING:
        logger.info(f"Deleted Logs({', '.join([str(i) for i in log_ids])})")
    return response.json()


def delete_log_fields(
    *,
    field: str,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    project: Optional[str] = None,
    context: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Deletes an entry from a log.

    Args:
        field: Name of the field to delete from the given logs.

        logs: log(s) to delete entries from.

        project: Name of the project to delete logs from.

        context: Context of the logs to delete entries from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A message indicating whether the log entries were successfully deleted.
    """
    log_ids = _to_log_ids(logs)
    api_key = _validate_api_key(api_key)
    headers = _create_request_header(api_key)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = context if context else CONTEXT_READ.get()
    body = {
        "project": project,
        "context": context,
        "ids_and_fields": [(log_ids, field)],
    }
    response = http.delete(
        BASE_URL + f"/logs",
        headers=headers,
        json=body,
    )
    if USR_LOGGING:
        logger.info(
            f"Deleted Field `{field}` from Logs({', '.join([str(i) for i in log_ids])})",
        )
    return response.json()


# noinspection PyShadowingBuiltins
def get_logs(
    *,
    project: Optional[str] = None,
    context: Optional[str] = None,
    column_context: Optional[str] = None,
    filter: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
    return_versions: Optional[bool] = None,
    group_threshold: Optional[int] = None,
    value_limit: Optional[int] = None,
    sorting: Optional[Dict[str, Any]] = None,
    group_sorting: Optional[Dict[str, Any]] = None,
    from_ids: Optional[List[int]] = None,
    exclude_ids: Optional[List[int]] = None,
    from_fields: Optional[List[str]] = None,
    exclude_fields: Optional[List[str]] = None,
    group_by: Optional[List[str]] = None,
    group_limit: Optional[int] = None,
    group_offset: Optional[int] = 0,
    group_depth: Optional[int] = None,
    nested_groups: Optional[bool] = True,
    groups_only: Optional[bool] = None,
    return_timestamps: Optional[bool] = None,
    return_ids_only: bool = False,
    api_key: Optional[str] = None,
) -> Union[List[unify.Log], Dict[str, Any]]:
    """
    Returns a list of filtered logs from a project.

    Args:
        project: Name of the project to get logs from.

        context: Context of the logs to get.

        column_context: Column context of the logs to get.

        filter: Boolean string to filter logs, for example:
        "(temperature > 0.5 and (len(system_msg) < 100 or 'no' in usr_response))"

        limit: The maximum number of logs to return. Default is None (unlimited).

        offset: The starting index of the logs to return. Default is 0.

        return_versions: Whether to return all versions of logs.

        group_threshold: Entries that appear in at least this many logs will be grouped together.

        value_limit: Maximum number of characters to return for string values.

        sorting: A dictionary specifying the sorting order for the logs by field names.

        group_sorting: A dictionary specifying the sorting order for the groups relative to each other based on aggregated metrics.

        from_ids: A list of log IDs to include in the results.

        exclude_ids: A list of log IDs to exclude from the results.

        from_fields: A list of field names to include in the results.

        exclude_fields: A list of field names to exclude from the results.

        group_by: A list of field names to group the logs by.

        group_limit: The maximum number of groups to return at each level.

        group_offset: Number of groups to skip at each level.

        group_depth: Maximum depth of nested groups to return.

        nested_groups: Whether to return nested groups.

        groups_only: Whether to return only the groups.

        return_timestamps: Whether to return the timestamps of the logs.

        return_ids_only: Whether to return only the log ids.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        The list of logs for the project, after optionally applying filtering.
    """
    # ToDo: add support for all context handlers
    api_key = _validate_api_key(api_key)
    headers = _create_request_header(api_key)
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    context = context if context else CONTEXT_READ.get()
    column_context = column_context if column_context else COLUMN_CONTEXT_READ.get()
    merged_filters = ACTIVE_ENTRIES_READ.get()
    if merged_filters:
        _filter = " and ".join(f"{k}=={repr(v)}" for k, v in merged_filters.items())
        if filter:
            filter = f"({filter}) and ({_filter})"
        else:
            filter = _filter
    params = {
        "project": project,
        "context": context,
        "filter_expr": filter,
        "limit": limit,
        "offset": offset,
        "return_ids_only": return_ids_only,
        "column_context": column_context,
        "return_versions": return_versions,
        "group_threshold": group_threshold,
        "value_limit": value_limit,
        "sorting": json.dumps(sorting) if sorting is not None else None,
        "group_sorting": (
            json.dumps(group_sorting) if group_sorting is not None else None
        ),
        "from_ids": "&".join(map(str, from_ids)) if from_ids else None,
        "exclude_ids": "&".join(map(str, exclude_ids)) if exclude_ids else None,
        "from_fields": "&".join(from_fields) if from_fields else None,
        "exclude_fields": "&".join(exclude_fields) if exclude_fields else None,
        "group_by": group_by,
        "group_limit": group_limit,
        "group_offset": group_offset,
        "group_depth": group_depth,
        "nested_groups": nested_groups,
        "groups_only": groups_only,
        "return_timestamps": return_timestamps,
    }

    response = http.get(BASE_URL + "/logs", headers=headers, params=params)

    if not group_by:
        if return_ids_only:
            return response.json()
        resp_data = response.json()
        logs_data = resp_data.get("logs", [])
        return [_create_log(dct, context, api_key) for dct in logs_data]

    resp_data = response.json()
    if nested_groups:
        logs_data = resp_data.get("logs", [])
        return _create_log_groups_nested(context, api_key, logs_data, {})
    else:
        groups = resp_data.get("groups", {})
        logs_data = resp_data.get("logs", [])
        return _create_log_groups_not_nested(logs_data, groups, context, api_key)


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
    headers = _create_request_header(api_key)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    response = http.get(
        BASE_URL + "/logs",
        params={"project": project, "from_ids": [id]},
        headers=headers,
    )
    resp_data = response.json()
    lgs = resp_data.get("logs", [])
    if len(lgs) == 0:
        raise Exception(f"Log with id {id} does not exist")
    lg = lgs[0]
    return unify.Log(
        id=lg["id"],
        ts=lg["ts"],
        **lg["entries"],
        **lg["derived_entries"],
        api_key=api_key,
    )


# noinspection PyShadowingBuiltins
def get_logs_metric(
    *,
    metric: str,
    key: Union[str, List[str]],
    filter: Optional[Union[str, Dict[str, str]]] = None,
    project: Optional[str] = None,
    context: Optional[str] = None,
    from_ids: Optional[Union[List[int], Dict[str, str]]] = None,
    exclude_ids: Optional[Union[List[int], Dict[str, str]]] = None,
    group_by: Optional[Union[str, List[str]]] = None,
    api_key: Optional[str] = None,
) -> Union[float, int, bool, str, Dict[str, Any]]:
    """
    Retrieve a set of log metrics across a project, after applying the filtering.

    This endpoint supports three modes of operation:

    1. Single key, no grouping: Returns a single metric value
       Example:
       get_logs_metric(metric="mean", key="score")
       Response: 4.56

    2. Multiple keys, no grouping: Returns a dict mapping keys to metric values
       Example:
       get_logs_metric(metric="mean", key=["score", "length"])
       Response: {"score": 4.56, "length": 120}

    3. With grouping: Returns metrics grouped by one or more fields
       Example:
       get_logs_metric(metric="mean", key="score", group_by="model")
       Response: {"gpt-4": 4.56, "gpt-3.5": 3.78}

       For nested grouping, provide a list of fields:
       Example:
       get_logs_metric(metric="mean", key="score", group_by=["model", "temperature"])
       Response: {"gpt-4": {"0.7": 4.56, "0.9": 4.23}, "gpt-3.5": {"0.7": 3.78, "0.9": 3.45}}

    Args:
        metric: The reduction metric to compute for the specified key(s). Supported are:
            sum, mean, var, std, min, max, median, mode.

        key: The key(s) to compute the reduction statistic for. Can be a single string
            for one key, or a list of strings for multiple keys.

        filter: The filtering to apply to the log values. Can be:
            - A single string expression for all keys, e.g.:
              "(temperature > 0.5 and (len(system_msg) < 100 or 'no' in usr_response))"
            - A dict mapping keys to filter expressions for key-specific filtering, e.g.:
              {"score": "score > 0", "length": "length < 100"}

        project: The id of the project to retrieve the logs for.

        context: The context of the logs to retrieve the metrics for.

        from_ids: Log IDs to include in the results. Can be:
            - A list of integers for all keys, e.g.: [1, 2, 3]
            - A dict mapping keys to ID strings for key-specific filtering, e.g.:
              {"score": "1&2", "length": "3&4"}

        exclude_ids: Log IDs to exclude from the results. Can be:
            - A list of integers for all keys, e.g.: [1, 2, 3]
            - A dict mapping keys to ID strings for key-specific filtering, e.g.:
              {"score": "1&2", "length": "3&4"}

        group_by: Field(s) to group the metrics by. Can be:
            - A single string for single-level grouping, e.g.: "model"
            - A list of strings for nested grouping, e.g.: ["model", "temperature"]
            Each field can be prefixed with "entries/" or "derived_entries/" for entry fields.

        api_key: If specified, unify API key to be used. Defaults to the value in the
            `UNIFY_KEY` environment variable.

    Returns:
        The metric value(s) for the project, after optionally applying filtering and grouping.
        Return type depends on the mode:
        - Single key, no grouping: scalar (float, int, bool, or str)
        - Multiple keys, no grouping: dict mapping keys to scalar values
        - With grouping: dict with nested structure based on grouping levels
    """
    api_key = _validate_api_key(api_key)
    headers = _create_request_header(api_key)
    project = _get_and_maybe_create_project(project, api_key=api_key)

    # Build params dict
    params = {
        "project": project,
        "context": context if context else CONTEXT_READ.get(),
    }

    # Handle key parameter - JSON encode if it's a list
    if isinstance(key, list):
        params["key"] = json.dumps(key)
    else:
        params["key"] = key

    # Handle filter_expr parameter - JSON encode if it's a dict
    if filter is not None:
        if isinstance(filter, dict):
            params["filter_expr"] = json.dumps(filter)
        else:
            params["filter_expr"] = filter

    # Handle from_ids parameter
    if from_ids is not None:
        if isinstance(from_ids, dict):
            # Key-specific from_ids - JSON encode the dict
            params["from_ids"] = json.dumps(from_ids)
        else:
            # Legacy format - join list with &
            params["from_ids"] = "&".join(map(str, from_ids))

    # Handle exclude_ids parameter
    if exclude_ids is not None:
        if isinstance(exclude_ids, dict):
            # Key-specific exclude_ids - JSON encode the dict
            params["exclude_ids"] = json.dumps(exclude_ids)
        else:
            # Legacy format - join list with &
            params["exclude_ids"] = "&".join(map(str, exclude_ids))

    # Handle group_by parameter - JSON encode if it's a list
    if group_by is not None:
        if isinstance(group_by, list):
            params["group_by"] = json.dumps(group_by)
        else:
            params["group_by"] = group_by

    response = http.get(
        BASE_URL + f"/logs/metric/{metric}",
        headers=headers,
        params=params,
    )
    return response.json()


def get_groups(
    *,
    key: str,
    project: Optional[str] = None,
    context: Optional[str] = None,
    filter: Optional[Dict[str, Any]] = None,
    from_ids: Optional[List[int]] = None,
    exclude_ids: Optional[List[int]] = None,
    api_key: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns a list of the different version/values of one entry within a given project
    based on its key.

    Args:
        key: Name of the log entry to do equality matching for.

        project: Name of the project to get logs from.

        context: The context to get groups from.

        filter: Boolean string to filter logs, for example:
        "(temperature > 0.5 and (len(system_msg) < 100 or 'no' in usr_response))"

        from_ids: A list of log IDs to include in the results.

        exclude_ids: A list of log IDs to exclude from the results.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A dict containing the grouped logs, with each key of the dict representing the
        version of the log key with equal values, and the value being the equal value.
    """
    api_key = _validate_api_key(api_key)
    headers = _create_request_header(api_key)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = context if context else CONTEXT_READ.get()
    params = {
        "project": project,
        "context": context,
        "key": key,
        "filter_expr": filter,
        "from_ids": from_ids,
        "exclude_ids": exclude_ids,
    }
    response = http.get(BASE_URL + "/logs/groups", headers=headers, params=params)
    return response.json()


def create_derived_logs(
    *,
    key: str,
    equation: str,
    referenced_logs,
    derived: Optional[bool] = None,
    project: Optional[str] = None,
    context: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates one or more entries based on equation and referenced_logs.

    Args:
        key: The name of the entry.
        equation: The equation for computing the value of each derived entry.
        referenced_logs: The logs to use for each newly created derived entry,
        either as a list of log ids or as a set of arguments for the get_logs endpoint.
        derived: Whether to create derived logs (True) or static entries in base logs (False).

    Returns:
        A message indicating whether the derived logs were successfully created.
    """
    api_key = _validate_api_key(api_key)
    headers = _create_request_header(api_key)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = context if context else CONTEXT_WRITE.get()
    body = {
        "project": project,
        "context": context,
        "key": key,
        "equation": equation,
        "referenced_logs": referenced_logs,
    }
    if derived is not None:
        body["derived"] = derived
    response = http.post(BASE_URL + "/logs/derived", headers=headers, json=body)
    return response.json()


def join_logs(
    *,
    pair_of_args: Tuple[Dict[str, Any], Dict[str, Any]],
    join_expr: str,
    mode: str,
    new_context: str,
    copy: Optional[bool] = True,
    columns: Optional[List[str]] = None,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
):
    """
    Join two sets of logs based on specified criteria and creates new logs with the joined data.
    """
    api_key = _validate_api_key(api_key)
    headers = _create_request_header(api_key)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    body = {
        "project": project,
        "pair_of_args": pair_of_args,
        "join_expr": join_expr,
        "mode": mode,
        "new_context": new_context,
        "columns": columns,
        "copy": copy,
    }
    response = http.post(BASE_URL + "/logs/join", headers=headers, json=body)
    return response.json()


def create_fields(
    fields: Union[Dict[str, Any], List[str]],
    *,
    backfill_logs: Optional[bool] = None,
    project: Optional[str] = None,
    context: Optional[str] = None,
    api_key: Optional[str] = None,
):
    """
    Creates one or more fields in a project.

    Args:
        fields: Dictionary mapping field names to their types (or None if no explicit type).

        project: Name of the project to create fields in.

        context: The context to create fields in.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.
    """
    api_key = _validate_api_key(api_key)
    headers = _create_request_header(api_key)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = context if context else CONTEXT_WRITE.get()
    if isinstance(fields, list):
        fields = {field: None for field in fields}
    body = {
        "project": project,
        "context": context,
        "fields": fields,
    }
    if backfill_logs is not None:
        body["backfill_logs"] = backfill_logs
    response = http.post(BASE_URL + "/logs/fields", headers=headers, json=body)
    return response.json()


def rename_field(
    name: str,
    new_name: str,
    *,
    project: Optional[str] = None,
    context: Optional[str] = None,
    api_key: Optional[str] = None,
):
    """
    Rename a field in a project.

    Args:
        name: The name of the field to rename.

        new_name: The new name for the field.

        project: Name of the project to rename the field in.

        context: The context to rename the field in.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.
    """
    api_key = _validate_api_key(api_key)
    headers = _create_request_header(api_key)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = context if context else CONTEXT_WRITE.get()
    body = {
        "project": project,
        "context": context,
        "old_field_name": name,
        "new_field_name": new_name,
    }
    response = http.patch(
        BASE_URL + "/logs/rename_field",
        headers=headers,
        json=body,
    )
    return response.json()


def get_fields(
    *,
    project: Optional[str] = None,
    context: Optional[str] = None,
    api_key: Optional[str] = None,
):
    """
    Get a dictionary of fields names and their types

    Args:
        project: Name of the project to get fields from.

        context: The context to get fields from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A dictionary of fields names and their types
    """
    api_key = _validate_api_key(api_key)
    headers = _create_request_header(api_key)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = context if context else CONTEXT_READ.get()
    params = {
        "project": project,
        "context": context,
    }
    response = http.get(BASE_URL + "/logs/fields", headers=headers, params=params)
    return response.json()


def delete_fields(
    fields: List[str],
    *,
    project: Optional[str] = None,
    context: Optional[str] = None,
    api_key: Optional[str] = None,
):
    """
    Delete one or more fields from a project.

    Args:
        fields: List of field names to delete.

        project: Name of the project to delete fields from.

        context: The context to delete fields from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.
    """
    api_key = _validate_api_key(api_key)
    headers = _create_request_header(api_key)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = context if context else CONTEXT_WRITE.get()
    body = {
        "project": project,
        "context": context,
        "fields": fields,
    }
    response = http.delete(
        BASE_URL + "/logs/fields",
        headers=headers,
        json=body,
    )
    return response.json()


def set_user_logging(value: bool):
    global USR_LOGGING
    USR_LOGGING = value
