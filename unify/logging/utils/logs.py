from __future__ import annotations

import asyncio
import atexit
import inspect
import json
import logging
import signal
import threading

import aiohttp

logger = logging.getLogger(__name__)
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
from types import ModuleType
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

# Tracing
ACTIVE_TRACE_LOG = ContextVar("active_trace_log", default=[])
ACTIVE_TRACE_PARAMETERS = ContextVar("active_trace_parameters", default=None)
TRACING_LOG_CONTEXT = None
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


class _TraceLogState:
    __slots__ = ("lock", "processing", "pending_value")

    def __init__(self) -> None:
        self.lock = asyncio.Lock()
        self.processing = False
        self.pending_value: Dict[str, Any] | None = None


class _AsyncTraceLogger:
    def __init__(self) -> None:
        self._states: dict[str, _TraceLogState] = {}
        self.stopped = False
        self._api_key = _validate_api_key(None)
        self._pending_submit_requests = 0

        atexit.register(self.shutdown, flush=True)
        signal.signal(signal.SIGINT, self._on_sigint)

        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        self._loop = asyncio.new_event_loop()
        self._loop.set_default_executor(
            ThreadPoolExecutor(thread_name_prefix="UnifyTraceLogger"),
        )
        self._client = aiohttp.ClientSession(loop=self._loop, headers=headers)
        self._thread = threading.Thread(
            name="UnifyTraceLogger",
            target=self._loop.run_forever,
            daemon=True,
        )
        self._thread.start()

    def update_trace(self, log: unify.Log, trace: dict):
        metadata = {
            "id": log.id,
            "project": unify.active_project(),
            "context": log.context,
        }
        fut = asyncio.run_coroutine_threadsafe(
            self._update_log(metadata, trace),
            self._loop,
        )
        self._pending_submit_requests += 1
        fut.add_done_callback(self._update_log_callback)

    def is_processing(self) -> bool:
        return self._pending_submit_requests > 0 or len(self._states) > 0

    def _update_log_callback(self, fut):
        self._pending_submit_requests -= 1

    def shutdown(self, flush: bool = True) -> None:
        if self.stopped:
            return
        self.stopped = True

        if flush:
            drain_future = asyncio.run_coroutine_threadsafe(
                self._drain(),
                self._loop,
            )
            from concurrent.futures import TimeoutError

            while True:
                try:
                    drain_future.result(
                        timeout=0.1,
                    )  # blocks until all requests are done
                except (asyncio.TimeoutError, TimeoutError):
                    continue
                else:
                    break
        else:
            asyncio.run_coroutine_threadsafe(
                self._shutdown_tasks(),
                self._loop,
            )

        close_future = asyncio.run_coroutine_threadsafe(
            self._close_client(),
            self._loop,
        )
        close_future.result()

        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join()
        self._loop.close()

    async def _update_log(self, log_metadata, trace) -> None:
        state = self._states.setdefault(log_metadata["id"], _TraceLogState())
        async with state.lock:
            state.pending_value = {
                "trace": trace,
                "project": log_metadata["project"],
                "context": log_metadata["context"],
            }
            if not state.processing:
                state.processing = True
                asyncio.create_task(self._process_log(log_metadata["id"], state))

    async def _process_log(self, log_id: int, state: _TraceLogState):
        try:
            while True:
                async with state.lock:
                    value = state.pending_value
                    state.pending_value = None

                if value is None:
                    async with state.lock:
                        state.processing = False
                    return

                try:
                    await self._send_request(log_id, value)
                except Exception as e:
                    logger.error(f"error updating trace {log_id!r}: {e}")

                if value["trace"].get("completed") == True:
                    async with state.lock:
                        state.processing = False
                    self._states.pop(log_id, None)
                    return
        except asyncio.CancelledError:
            pass

    async def _send_request(self, log_id: str, value: Dict[str, Any]):
        entries = {"trace": value["trace"]}
        entries = _apply_col_context(**entries)
        entries = {**entries, **ACTIVE_ENTRIES_WRITE.get()}
        entries = _handle_special_types(entries)
        entries = _handle_mutability(True, entries)

        body = {
            "logs": [log_id],
            "project": value["project"],
            "context": value["context"],
            "entries": entries,
            "overwrite": True,
        }

        async with self._client.put(
            f"{BASE_URL}/logs",
            json=body,
        ) as resp:
            resp.raise_for_status()

    async def _drain(self):
        while any(state.processing for state in self._states.values()):
            await asyncio.sleep(0.05)

    async def _shutdown_tasks(self):
        for task in self.tasks:
            await task.cancel()

    async def _close_client(self):
        await self._client.close()
        await asyncio.sleep(1)

    def _on_sigint(self, signum, frame):
        self.shutdown(flush=False)
        exit(0)


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


def initialize_trace_logger():
    """
    Initialize the trace logger. Must be called from the main thread.
    """
    global _trace_logger
    if _trace_logger is None:
        _trace_logger = _AsyncTraceLogger()


def _get_trace_logger():
    return _trace_logger


def _set_active_trace_parameters(
    prune_empty: bool = True,
    span_type: str = "function",
    name: Optional[str] = None,
    filter: Optional[Callable[[callable], bool]] = None,
    fn_type: Optional[str] = None,
    recursive: bool = False,  # Only valid for Functions.
    depth: Optional[int] = None,
    skip_modules: Optional[List[ModuleType]] = None,
    skip_functions: Optional[List[Callable]] = None,
):
    token = ACTIVE_TRACE_PARAMETERS.set(
        {
            "prune_empty": prune_empty,
            "span_type": span_type,
            "name": name,
            "filter": filter,
            "fn_type": fn_type,
            "recursive": recursive,
            "depth": depth,
            "skip_modules": skip_modules,
            "skip_functions": skip_functions,
        },
    )
    return token


def _reset_active_trace_parameters(token):
    ACTIVE_TRACE_PARAMETERS.reset(token)


def set_trace_context(context: str):
    global TRACING_LOG_CONTEXT
    ctx_wrt = CONTEXT_WRITE.get()
    if ctx_wrt:
        if context:
            context = f"{ctx_wrt}/{context}"
        else:
            context = ctx_wrt
    TRACING_LOG_CONTEXT = context
    if context is None:
        return
    names = [name for name, _ in unify.get_contexts().items()]
    if context not in names:
        unify.create_context(name=context)


def get_trace_context():
    global TRACING_LOG_CONTEXT
    return TRACING_LOG_CONTEXT


def mark_spans_as_done(
    log_ids: Optional[Union[int, List[int]]] = None,
    span_ids: Optional[Union[str, List[str]]] = None,
    *,
    project: Optional[str] = None,
    contexts: Optional[Union[str, List[str]]] = None,
):
    """
    Marks all of the listed span ids for the listed logs in the listed contexts as completed.
    In all cases of this specification hierarchy, if none are provided then all associated spans are marked as complete.
    """
    if log_ids is not None:
        log_ids = [log_ids] if isinstance(log_ids, int) else log_ids

    if span_ids is not None:
        span_ids = [span_ids] if isinstance(span_ids, str) else span_ids

    def _traverse_trace_and_mark_done(trace: dict):
        if span_ids is None:
            trace["completed"] = True
        elif trace["id"] in span_ids:
            trace["completed"] = True

        for span in trace["child_spans"]:
            _traverse_trace_and_mark_done(span)

    if log_ids:
        logs = unify.get_logs(project=project, context=contexts, from_ids=log_ids)
    else:
        if isinstance(contexts, list):
            logs = []
            for context in contexts:
                logs.extend(
                    unify.get_logs(
                        project=project,
                        context=context,
                        from_fields=["trace"],
                        filter=f"trace != None",
                    ),
                )
        else:
            logs = unify.get_logs(
                project=project,
                context=contexts,
                from_fields=["trace"],
                filter=f"trace != None",
            )

    for log in logs:
        _traverse_trace_and_mark_done(log.entries["trace"])
        unify.update_logs(
            logs=log.id,
            entries={"trace": log.entries["trace"]},
            overwrite=True,
        )


def _apply_row_ids(
    row_ids_data: Optional[Dict[str, Any]], entries: List[Dict[str, Any]]
) -> None:
    """
    Apply row_ids data from server response to entry dictionaries.

    Handles the new standardized format {'names': List[str], 'ids': List[List[int]]}
    while maintaining backward compatibility with the old format during transition.

    Args:
        row_ids_data: The row_ids data from server response
        entries: List of entry dictionaries to update with row_ids
    """
    if not row_ids_data:
        return

    names = row_ids_data.get("names")
    ids = row_ids_data.get("ids")

    if not names or not ids:
        return

    # Ensure names is always treated as a list for consistent processing
    if not isinstance(names, list):
        names = [names]

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

    created_log.entries.pop("explicit_types", None)

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
    resp_json = response.json()

    # Apply row_ids to entries using the centralized helper
    _apply_row_ids(resp_json.get("row_ids"), [entries])

    return unify.Log(
        id=resp_json["log_event_ids"][0],
        api_key=api_key,
        **entries,
        params=params,
        context=context,
    )


def _create_log(dct, params, context, api_key, context_entries=None):
    if context_entries is None:
        context_entries = {}
    return unify.Log(
        id=dct["id"],
        ts=dct["ts"],
        **dct["entries"],
        **dct["derived_entries"],
        **context_entries,
        params={
            param_name: (param_ver, params[param_name][param_ver])
            for param_name, param_ver in dct["params"].items()
        },
        context=context,
        api_key=api_key,
    )


def _create_log_groups_nested(
    params,
    context,
    api_key,
    node,
    context_entries,
    prev_key=None,
):
    if isinstance(node, dict) and "group" not in node:
        ret = unify.LogGroup(list(node.keys())[0])
        ret.value = _create_log_groups_nested(
            params,
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
                        item["params"],
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
                    params,
                    context,
                    api_key,
                    n["value"],
                    context_entries,
                    n["key"],
                )
            return ret


def _create_log_groups_not_nested(logs, groups, params, context, api_key):
    logs_mapping = {}
    for dct in logs:
        logs_mapping[dct["id"]] = _create_log(dct, params, context, api_key)

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

        entries: List of dictionaries with the entries to be logged. For contexts with
        nested unique IDs, parent ID values can be passed directly in the entries
        dictionaries. For example, if a context has unique IDs `["run_id", "step_id"]`,
        you can pass `{"run_id": 0, "data": "value"}` in entries to generate the next
        `step_id` for that particular run. The leftmost N-1 unique columns can be
        supplied as normal entry keys, and the rightmost column is always auto-incremented.

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
        resp_json = response.json()

        # Apply row_ids to entries using the centralized helper
        _apply_row_ids(resp_json.get("row_ids"), entries)

        return [
            unify.Log(
                project=project,
                context=context["name"] if isinstance(context, dict) else context,
                **{k: v for k, v in e.items() if k != "explicit_types"},
                **p,
                id=i,
            )
            for e, p, i in zip(entries, params, resp_json["log_event_ids"])
        ]

    # Fallback for non-batched (iterative) logging
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
        mode="entries",
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
    log_ids = _to_log_ids(logs)
    body = {
        "logs": log_ids,
        "context": context,
        "overwrite": overwrite,
    }
    if entries is not None:
        body["entries"] = entries
    if params is not None:
        body["params"] = params
    response = _requests.put(BASE_URL + "/logs", headers=headers, json=body)
    _check_response(response)
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
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {
        "project": project,
        "context": context,
        "ids_and_fields": [(log_ids, None)],
        "source_type": source_type,
    }
    params = {"delete_empty_logs": delete_empty_logs}
    response = _requests.delete(
        BASE_URL + "/logs",
        headers=headers,
        params=params,
        json=body,
    )
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

    response = _requests.get(BASE_URL + "/logs", headers=headers, params=params)
    _check_response(response)

    if not group_by:
        if return_ids_only:
            return response.json()
        params, logs, _ = response.json().values()
        return [_create_log(dct, params, context, api_key) for dct in logs]

    if nested_groups:
        params, logs, _ = response.json().values()
        return _create_log_groups_nested(params, context, api_key, logs, {})
    else:
        params, groups, logs, _ = response.json().values()
        return _create_log_groups_not_nested(logs, groups, params, context, api_key)


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
    context: Optional[str] = None,
    from_ids: Optional[List[int]] = None,
    exclude_ids: Optional[List[int]] = None,
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

        context: The context of the logs to retrieve the metrics for.

        from_ids: A list of log IDs to include in the results.

        exclude_ids: A list of log IDs to exclude from the results.

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
    params = {
        "project": project,
        "filter_expr": filter,
        "key": key,
        "from_ids": "&".join(map(str, from_ids)) if from_ids else None,
        "exclude_ids": "&".join(map(str, exclude_ids)) if exclude_ids else None,
        "context": context if context else CONTEXT_READ.get(),
    }
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
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    project = _get_and_maybe_create_project(project, api_key=api_key)
    params = {
        "project": project,
        "key": key,
        "filter_expr": filter,
        "from_ids": from_ids,
        "exclude_ids": exclude_ids,
    }
    response = _requests.get(BASE_URL + "/logs/groups", headers=headers, params=params)
    _check_response(response)
    return response.json()


def get_logs_latest_timestamp(
    *,
    project: Optional[str] = None,
    context: Optional[str] = None,
    column_context: Optional[str] = None,
    filter: Optional[str] = None,
    sort_by: Optional[str] = None,
    from_ids: Optional[List[int]] = None,
    exclude_ids: Optional[List[int]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    api_key: Optional[str] = None,
) -> int:
    """
    Returns the update timestamp of the most recently updated log within the specified page and filter bounds.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = context if context else CONTEXT_READ.get()
    column_context = column_context if column_context else COLUMN_CONTEXT_READ.get()
    params = {
        "project": project,
        "context": context,
        "column_context": column_context,
        "filter_expr": filter,
        "sort_by": sort_by,
        "from_ids": "&".join(map(str, from_ids)) if from_ids else None,
        "exclude_ids": "&".join(map(str, exclude_ids)) if exclude_ids else None,
        "limit": limit,
        "offset": offset,
    }
    response = _requests.get(
        BASE_URL + "/logs/latest_timestamp",
        headers=headers,
        params=params,
    )
    _check_response(response)
    return response.json()


def update_derived_log(
    *,
    target: Union[List[int], Dict[str, str]],
    key: Optional[str] = None,
    equation: Optional[str] = None,
    referenced_logs: Optional[List[int]] = None,
    project: Optional[str] = None,
    context: Optional[str] = None,
    api_key: Optional[str] = None,
) -> None:
    """
    Update the derived entries for a log.

    Args:
        target: The derived logs to update

        key: New key name for the derived entries

        equation: New equation for computing derived values

        referenced_logs: Optional new referenced logs to use for computation.

        project: The project to update the derived logs for

        context: The context to update the derived logs for

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A message indicating whether the derived logs were successfully updated.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = context if context else CONTEXT_WRITE.get()
    body = {
        "project": project,
        "context": context,
        "target_derived_logs": target,
        "key": key,
        "equation": equation,
        "referenced_logs": referenced_logs,
    }
    response = _requests.put(BASE_URL + "/logs/derived", headers=headers, json=body)
    _check_response(response)
    return response.json()


def join_logs(
    *,
    pair_of_args: List[Dict[str, Any]],
    join_expr: str,
    mode: str,
    new_context: str,
    columns: Optional[List[str]] = None,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
):
    """
    Join two sets of logs based on specified criteria and creates new logs with the joined data.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    project = _get_and_maybe_create_project(project, api_key=api_key)
    params = {
        "project": project,
        "pair_of_args": pair_of_args,
        "join_expr": join_expr,
        "mode": mode,
        "new_context": new_context,
        "columns": columns,
    }
    response = _requests.post(BASE_URL + "/logs/join", headers=headers, params=params)
    _check_response(response)
    return response.json()


def create_fields(
    fields: Union[Dict[str, Any], List[str]],
    *,
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
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = context if context else CONTEXT_WRITE.get()
    if isinstance(fields, list):
        fields = {field: None for field in fields}
    body = {
        "project": project,
        "context": context,
        "fields": fields,
    }
    response = _requests.post(BASE_URL + "/logs/fields", headers=headers, json=body)
    _check_response(response)
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
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = context if context else CONTEXT_WRITE.get()
    body = {
        "project": project,
        "context": context,
        "old_field_name": name,
        "new_field_name": new_name,
    }
    response = _requests.patch(
        BASE_URL + "/logs/rename_field",
        headers=headers,
        json=body,
    )
    _check_response(response)
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
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = context if context else CONTEXT_READ.get()
    params = {
        "project": project,
        "context": context,
    }
    response = _requests.get(BASE_URL + "/logs/fields", headers=headers, params=params)
    _check_response(response)
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
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    project = _get_and_maybe_create_project(project, api_key=api_key)
    context = context if context else CONTEXT_WRITE.get()
    body = {
        "project": project,
        "context": context,
        "fields": fields,
    }
    response = _requests.delete(
        BASE_URL + "/logs/fields",
        headers=headers,
        json=body,
    )
    _check_response(response)
    return response.json()


# User Logging #
# -------------#


def set_user_logging(value: bool):
    global USR_LOGGING
    USR_LOGGING = value
