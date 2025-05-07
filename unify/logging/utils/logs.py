from __future__ import annotations

import atexit
import inspect
import json
import logging
import queue
import threading

logger = logging.getLogger(__name__)
import os
import sys
from contextvars import ContextVar
from typing import Any, Callable, Dict, List, Optional, Union

import unify
from tqdm import tqdm
from unify import BASE_URL
from unify.utils import _requests
from unify.utils.helpers import flexible_deepcopy

from ...utils._caching import (
    _get_cache,
    _get_caching,
    _get_caching_fname,
    _write_to_cache,
)
from ...utils.helpers import (
    _check_response,
    _get_and_maybe_create_project,
    _validate_api_key,
)
from .async_logger import AsyncLoggerManager

# logging configuration
USR_LOGGING = True
ASYNC_LOGGING = False  # Flag to enable/disable async logging
ASYNC_BATCH_SIZE = 100  # Default batch size for async logging
ASYNC_FLUSH_INTERVAL = 5.0  # Default flush interval in secondss
ASYNC_MAX_QUEUE_SIZE = 10000  # Default maximum queue size

# Async logger instance
_async_logger: Optional[AsyncLoggerManager] = None
_trace_logger: Optional[_AsyncTraceLogger] = None

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

# params
ACTIVE_PARAMS_WRITE = ContextVar(
    "active_params_write",
    default={},
)
ACTIVE_PARAMS_READ = ContextVar(
    "active_params_read",
    default={},
)
ACTIVE_PARAMS_MODE = ContextVar("active_params_mode", default="both")
PARAMS_NEST_LEVEL = ContextVar("params_nest_level", default=0)

# span
GLOBAL_SPAN = ContextVar("global_span", default={})
SPAN = ContextVar("span", default={})
RUNNING_TIME = ContextVar("running_time", default=0.0)

# chunking
CHUNK_LIMIT = 5000000


class _AsyncTraceLogger(threading.Thread):
    class _StopEvent:
        pass

    def __init__(self):
        super().__init__(name="TraceLoggerThread", daemon=True)
        self.queue = queue.Queue()
        self.start()
        atexit.register(self.stop)

    def run(self):
        while True:
            item = self.queue.get()
            if isinstance(item, self._StopEvent):
                break

            log_id, trace = item
            unify.add_log_entries(logs=log_id, trace=trace, overwrite=True)

    def update_trace(self, log_id, trace):
        self.queue.put_nowait((log_id, trace))

    def stop(self):
        """Stop normally, waiting for queue to be processed"""
        self.queue.put_nowait(self._StopEvent())
        while self.is_alive():
            try:
                self.join(timeout=0.1)
            except KeyboardInterrupt:
                self.stop_immediate()
                raise

    def stop_immediate(self):
        """Stop immediately, ignoring remaining queue items"""
        self.queue = queue.Queue()
        self.queue.put_nowait(self._StopEvent())
        self.join()


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


def initialize_async_logger(
    api_key: Optional[str] = None,
) -> None:
    """
    Initialize the async logger with the specified configuration.

    Args:
        batch_size: Number of logs to batch together before sending
        flush_interval: How often to flush logs in seconds
        max_queue_size: Maximum size of the log queue
        api_key: API key for authentication
    """
    global _async_logger, ASYNC_LOGGING

    if _async_logger is not None:
        return
    api_key = _validate_api_key(api_key)
    _async_logger = AsyncLoggerManager(
        base_url=BASE_URL,
        api_key=api_key,
    )
    ASYNC_LOGGING = True

    # Register shutdown handler
    atexit.register(shutdown_async_logger)


def shutdown_async_logger(immediate=False) -> None:
    """
    Gracefully shutdown the async logger, ensuring all pending logs are flushed.
    """
    global _async_logger, ASYNC_LOGGING

    if _async_logger is not None:
        _async_logger.stop_sync(immediate=immediate)
        _async_logger = None
        ASYNC_LOGGING = False


def _initialize_trace_logger():
    global _trace_logger
    if _trace_logger is None:
        _trace_logger = _AsyncTraceLogger()


def _get_trace_logger():
    return _trace_logger


def _handle_cache(fn: Callable) -> Callable:
    def wrapped(*args, **kwargs):
        if not _get_caching():
            return fn(*args, **kwargs)
        kw_for_key = flexible_deepcopy(kwargs)
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
        for field, mut in mutable.items():
            for item in new_data:
                if field in item:
                    item.setdefault("explicit_types", {})[field] = {"mutable": mut}
    elif isinstance(mutable, bool):
        for item in new_data:
            for k in list(item.keys()):
                if k != "explicit_types":
                    item.setdefault("explicit_types", {})[k] = {"mutable": mutable}
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
    fn: Optional[Callable] = None,
    *,
    project: Optional[str] = None,
    context: Optional[str] = None,
    params: Dict[str, Any] = None,
    new: bool = False,
    overwrite: bool = False,
    mutable: Optional[Union[bool, Dict[str, bool]]] = True,
    api_key: Optional[str] = None,
    **entries,
) -> Union[unify.Log, Callable]:
    """
    Can be used either as a regular function to create logs or as a decorator to log function inputs, intermediates and outputs.

    When used as a regular function:
    Creates one or more logs associated to a project. unify.Logs are LLM-call-level data
    that might depend on other variables.

    When used as a decorator:
    Logs function inputs and intermediate values.

    Args:
        fn: When used as a decorator, this is the function to be wrapped.
        project: Name of the project the stored logs will be associated to.

        context: Context for the logs.

        params: Dictionary containing one or more key:value pairs that will be
        logged into the platform as params.

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
        When used as a regular function: The unique id of newly created log.
        When used as a decorator: The wrapped function.
    """
    # If used as a decorator
    if fn is not None and callable(fn):
        from unify.logging.logs import log_decorator

        if inspect.iscoroutinefunction(fn):

            async def async_wrapper(*args, **kwargs):
                transformed = log_decorator(fn)
                return await transformed(*args, **kwargs)

            return async_wrapper
        transformed = log_decorator(fn)
        return transformed

    # Regular log function logic
    global ASYNC_LOGGING
    api_key = _validate_api_key(api_key)
    context = _handle_context(context)
    if not new and ACTIVE_LOG.get():
        _add_to_log(
            context=context,
            mode="entries",
            overwrite=overwrite,
            mutable=mutable,
            api_key=api_key,
            **entries,
        )
        _add_to_log(
            context=context,
            mode="params",
            overwrite=overwrite,
            mutable=mutable,
            api_key=api_key,
            **(params if params is not None else {}),
        )
        log = ACTIVE_LOG.get()[-1]
        if USR_LOGGING:
            logger.info(f"Updated Log({log.id})")
        return log
    # Process parameters and entries
    params = _apply_col_context(**(params if params else {}))
    params = {**params, **ACTIVE_PARAMS_WRITE.get()}
    params = _handle_special_types(params)
    params = _handle_mutability(mutable, params)
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
            params=params,
            entries=entries,
        )
        created_log = unify.Log(
            id=None,  # Placeholder; will be updated when the Future resolves.
            _future=log_future,
            api_key=api_key,
            **entries,
            params=params,
            context=context,
        )
    else:
        # Use synchronous logging
        created_log = _sync_log(
            project=project,
            context=context,
            params=params,
            entries=entries,
            api_key=api_key,
        )

    if PARAMS_NEST_LEVEL.get() > 0 or ENTRIES_NEST_LEVEL.get() > 0:
        LOGGED.set(
            {
                **LOGGED.get(),
                created_log.id: list(params.keys()) + list(entries.keys()),
            },
        )
    if USR_LOGGING:
        logger.info(f"Created Log({created_log.id})")
    return created_log


def _sync_log(
    project: str,
    context: Optional[str],
    params: Dict[str, Any],
    entries: Dict[str, Any],
    api_key: str,
) -> unify.Log:
    """
    Synchronously create a log entry using direct HTTP request.

    This is a helper function used when async logging is disabled or unavailable.
    """
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    body = {
        "project": project,
        "context": context,
        "params": params,
        "entries": entries,
    }
    response = _requests.post(BASE_URL + "/logs", headers=headers, json=body)
    _check_response(response)
    return unify.Log(
        id=response.json()["log_event_ids"][0],
        api_key=api_key,
        **entries,
        params=params,
        context=context,
    )


def create_logs(
    *,
    project: Optional[str] = None,
    context: Optional[str] = None,
    params: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None,
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

        entries: List of dictionaries with the entries to be logged.

        params: List of dictionaries with the params to be logged.

        mutable: Either a boolean to apply uniform mutability for all fields, or a dictionary mapping field names to booleans for per-field control. Defaults to True.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A list of the created logs.
    """
    api_key = _validate_api_key(api_key)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = _handle_context(context)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    # ToDo: add support for all of the context variables, as is done for `unify.log` above
    params = _handle_mutability(mutable, params)
    entries = _handle_mutability(mutable, entries)
    # ToDo remove the params/entries logic above once this [https://app.clickup.com/t/86c25g263] is done
    params = [{}] * len(entries) if params in [None, []] else params
    entries = [{}] * len(params) if entries in [None, []] else entries
    # end ToDo
    body = {
        "project": project,
        "context": context,
        "params": params,
        "entries": entries,
    }
    body_size = sys.getsizeof(json.dumps(body))
    if batched is None:
        batched = body_size < CHUNK_LIMIT
    if batched:
        if body_size < CHUNK_LIMIT:
            response = _requests.post(BASE_URL + "/logs", headers=headers, json=body)
        else:
            response = _requests.post(
                BASE_URL + "/logs",
                headers=headers,
                data=_json_chunker(body),
            )
        _check_response(response)
        return [
            unify.Log(
                project=project,
                context=context,
                **{k: v for k, v in e.items() if k != "explicit_types"},
                **p,
                id=i,
            )
            for e, p, i in zip(entries, params, response.json()["log_event_ids"])
        ]

    pbar = tqdm(total=len(params), unit="logs", desc="Creating Logs")
    try:
        unify.initialize_async_logger()
        _async_logger.register_callback(lambda: pbar.update(1))
        ret = []

        for p, e in zip(params, entries):
            ret.append(
                log(
                    project=project,
                    context=context,
                    params=p,
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
    mode: str = None,
    overwrite: bool = False,
    mutable: Optional[Union[bool, Dict[str, bool]]] = True,
    api_key: Optional[str] = None,
    **data,
) -> Dict[str, str]:
    assert mode in ("params", "entries"), "mode must be one of 'params', 'entries'"
    data = _apply_col_context(**data)
    nest_level = {"params": PARAMS_NEST_LEVEL, "entries": ENTRIES_NEST_LEVEL}[mode]
    active = {"params": ACTIVE_PARAMS_WRITE, "entries": ACTIVE_ENTRIES_WRITE}[mode]
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
            mode=mode,
            overwrite=overwrite,
            data=data,
        )
        return {"detail": "Update queued asynchronously"}
    else:
        # Fallback to synchronous update if async logging isn’t enabled.
        log_ids = _to_log_ids(logs)
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        all_kwargs = []
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
            assert all(
                kw == all_kwargs[0] for kw in all_kwargs
            ), "All logs must share the same context if they're all being updated at the same time."
            data = all_kwargs[0]
        body = {"logs": log_ids, mode: data, "overwrite": overwrite, "context": context}
        response = _requests.put(BASE_URL + "/logs", headers=headers, json=body)
        _check_response(response)
        if nest_level.get() > 0:
            logged = LOGGED.get()
            new_logged = {}
            for log_id in log_ids:
                if log_id in logged:
                    new_logged[log_id] = logged[log_id] + list(data.keys())
                else:
                    new_logged[log_id] = list(data.keys())
            LOGGED.set({**logged, **new_logged})
        return response.json()


def add_log_params(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    mutable: Optional[Union[bool, Dict[str, bool]]] = True,
    api_key: Optional[str] = None,
    **params,
) -> Dict[str, str]:
    """
    Add extra params into an existing log.

    Args:
        logs: The log(s) to update with extra params. Looks for the current active log if
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
        logger.info(
            f"Added Params {', '.join(list(params.keys()))} "
            f"to [Logs({', '.join([str(i) for i in _to_log_ids(logs)])})]",
        )
    return ret


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
        mode="entries",
        overwrite=overwrite,
        mutable=mutable,
        api_key=api_key,
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
    params: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
    entries: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
    overwrite: bool = False,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Updates existing logs.
    """
    if not logs and not params and not entries:
        return {"detail": "No logs to update."}
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {
        "logs": _to_log_ids(logs),
        "context": context,
        # ToDo: remove once this [https://app.clickup.com/t/86c25g263] is done
        "params": [{}] * len(entries) if params is None else params,
        "entries": [{}] * len(params) if entries is None else entries,
        # end ToDo
        "overwrite": overwrite,
    }
    response = _requests.put(BASE_URL + "/logs", headers=headers, json=body)
    _check_response(response)
    return response.json()


def delete_logs(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    project: Optional[str] = None,
    context: Optional[str] = None,
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
        logs = get_logs(project=project, context=context, api_key=api_key)
        if not logs:
            return {"message": "No logs to delete"}
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = context if context else CONTEXT_READ.get()
    log_ids = _to_log_ids(logs)
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {
        "project": project,
        "context": context,
        "ids_and_fields": [(log_ids, None)],
    }
    response = _requests.delete(BASE_URL + f"/logs", headers=headers, json=body)
    _check_response(response)
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
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = context if context else CONTEXT_READ.get()
    body = {
        "project": project,
        "context": context,
        "ids_and_fields": [(log_ids, field)],
    }
    response = _requests.delete(
        BASE_URL + f"/logs",
        headers=headers,
        json=body,
    )
    _check_response(response)
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
    return_ids_only: bool = False,
    api_key: Optional[str] = None,
) -> List[unify.Log]:
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

        return_ids_only: Whether to return only the log ids.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        The list of logs for the project, after optionally applying filtering.
    """
    # ToDo: add support for all context handlers
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = context if context else CONTEXT_READ.get()
    column_context = column_context if column_context else COLUMN_CONTEXT_READ.get()
    merged_filters = ACTIVE_PARAMS_READ.get() | ACTIVE_ENTRIES_READ.get()
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
    }
    response = _requests.get(BASE_URL + "/logs", headers=headers, params=params)
    _check_response(response)
    if return_ids_only:
        return response.json()
    params, logs, _ = response.json().values()
    return [
        unify.Log(
            id=dct["id"],
            ts=dct["ts"],
            **dct["entries"],
            **dct["derived_entries"],
            params={
                param_name: (param_ver, params[param_name][param_ver])
                for param_name, param_ver in dct["params"].items()
            },
            context=context,
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
    response = _requests.get(
        BASE_URL + "/logs",
        params={"project": project, "from_ids": [id]},
        headers=headers,
    )
    _check_response(response)
    params, lgs, count = response.json().values()
    if len(lgs) == 0:
        raise Exception(f"Log with id {id} does not exist")
    lg = lgs[0]
    return unify.Log(
        id=lg["id"],
        ts=lg["ts"],
        **lg["entries"],
        **lg["derived_entries"],
        params={k: (v, params[k][v]) for k, v in lg["params"].items()},
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
    response = _requests.get(
        BASE_URL + f"/logs/metric/{metric}",
        headers=headers,
        params=params,
    )
    _check_response(response)
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
    response = _requests.get(BASE_URL + "/logs/groups", headers=headers, params=params)
    _check_response(response)
    return response.json()


# User Logging #
# -------------#


def set_user_logging(value: bool):
    global USR_LOGGING
    USR_LOGGING = value
