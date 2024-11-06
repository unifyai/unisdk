from __future__ import annotations
import time
import uuid
import datetime

from ..utils.helpers import _validate_api_key, _prune_dict
from .utils.logging import _handle_special_types
from .utils.compositions import *


# Log #
# ----#


# noinspection PyShadowingBuiltins
class Log:

    def __init__(
        self,
        *,
        id: int = None,
        timestamp: Optional[datetime] = None,
        project: Optional[str] = None,
        api_key: Optional[str] = None,
        params: Dict[str, Any] = None,
        **entries,
    ):
        self._id = id
        self._timestamp = timestamp
        self._project = project
        self._entries = entries
        self._params = params
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
    def params(self) -> Dict[str, Any]:
        return self._params

    # Dunders

    def __eq__(self, other: Union[dict, Log]) -> bool:
        if isinstance(other, dict):
            other = Log(id=other["id"], **other["entries"])
        return self._id == other._id

    def __len__(self):
        return len(self._entries) + len(self._params)

    def __repr__(self) -> str:
        return f"Log(id={self._id})"

    # Public

    def download(self):
        self._entries = get_log_by_id(id=self._id, api_key=self._api_key)._entries

    def add_entries(self, **entries) -> None:
        add_log_entries(logs=self._id, api_key=self._api_key, **entries)
        self._entries = {**self._entries, **entries}

    def replace_entries(self, **entries) -> None:
        replace_log_entries(logs=self._id, api_key=self._api_key, **entries)
        self._entries = {**self._entries, **entries}

    def update_entries(self, fn, **entries) -> None:
        update_log_entries(fn=fn, log=self._id, api_key=self._api_key, **entries)
        for k, v in entries.items():
            f = fn[k] if isinstance(fn, dict) else fn
            self._entries[k] = f(self._entries[k], v)

    def rename_entries(self, **entries) -> None:
        rename_log_entries(logs=self._id, api_key=self._api_key, **entries)
        for old_name, new_name in entries.items():
            self._entries[new_name] = self._entries[old_name]
            del self._entries[old_name]

    def delete_entries(
        self,
        keys_to_delete: List[str],
    ) -> None:
        for key in keys_to_delete:
            delete_log_fields(field=key, logs=self._id, api_key=self._api_key)
            del self._entries[key]

    def delete(self) -> None:
        delete_logs(logs=self._id, api_key=self._api_key)

    def to_json(self):
        return {
            "id": self._id,
            "timestamp": self._timestamp,
            "entries": self._entries,
            "params": self._params,
            "api_key": self._api_key,
        }

    @staticmethod
    def from_json(state):
        entries = state["entries"]
        del state["entries"]
        state = {**state, **entries}
        return Log(**state)

    # Context #

    def __enter__(self):
        lg = unify.log(
            project=self._project,
            new=True,
            api_key=self._api_key,
            **self._entries,
        )
        self._active_log_set = False
        self._log_token = ACTIVE_LOG.set(ACTIVE_LOG.get() + [lg])
        self._id = lg.id
        self._timestamp = lg.timestamp

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.download()
        ACTIVE_LOG.reset(self._log_token)


class Context:

    def __init__(self, context: str):
        self._context = context

    def __enter__(self):
        self._context_token = CONTEXT.set(
            os.path.join(CONTEXT.get(), self._context),
        )

    def __exit__(self, *args, **kwargs):
        CONTEXT.reset(self._context_token)


class Entries:

    def __init__(self, **entries):
        self._entries = _handle_special_types(entries)

    def __enter__(self):
        self._entries_token = ACTIVE_ENTRIES.set(
            {**ACTIVE_ENTRIES.get(), **self._entries},
        )
        self._nest_token = ENTRIES_NEST_LEVEL.set(
            ENTRIES_NEST_LEVEL.get() + 1,
        )

    def __exit__(self, *args, **kwargs):
        ACTIVE_ENTRIES.reset(self._entries_token)
        ENTRIES_NEST_LEVEL.reset(self._nest_token)
        if ENTRIES_NEST_LEVEL.get() == 0:
            LOGGED.set({})


class Params:

    def __init__(self, **params):
        self._params = _handle_special_types(params)

    def __enter__(self):
        self._params_token = ACTIVE_PARAMS.set(
            {**ACTIVE_PARAMS.get(), **self._params},
        )
        self._nest_token = PARAMS_NEST_LEVEL.set(
            PARAMS_NEST_LEVEL.get() + 1,
        )

    def __exit__(self, *args, **kwargs):
        ACTIVE_PARAMS.reset(self._params_token)
        PARAMS_NEST_LEVEL.reset(self._nest_token)
        if PARAMS_NEST_LEVEL.get() == 0:
            LOGGED.set({})


class Experiment:

    def __init__(self, name: str):
        self._name = name

    def __enter__(self):
        self._params_token = ACTIVE_PARAMS.set(
            {**ACTIVE_PARAMS.get(), **{"experiment": self._name}},
        )
        self._nest_token = PARAMS_NEST_LEVEL.set(
            PARAMS_NEST_LEVEL.get() + 1,
        )

    def __exit__(self, *args, **kwargs):
        ACTIVE_PARAMS.reset(self._params_token)
        PARAMS_NEST_LEVEL.reset(self._nest_token)
        if PARAMS_NEST_LEVEL.get() == 0:
            LOGGED.set({})


# Tracing #
# --------#


def traced(fn: callable = None, *, prune_empty: bool = True):

    if fn is None:
        return lambda f: traced(f, prune_empty=prune_empty)

    def wrapped(*args, **kwargs):
        log_token = None if ACTIVE_LOG.get() else ACTIVE_LOG.set([unify.log()])
        t1 = time.perf_counter()
        if not SPAN.get():
            RUNNING_TIME.set(t1)
        signature = inspect.signature(fn)
        bound_args = signature.bind(*args, **kwargs)
        bound_args.apply_defaults()
        inputs = bound_args.arguments
        new_span = {
            "id": str(uuid.uuid4()),
            "parent_span_id": (None if not SPAN.get() else SPAN.get()["id"]),
            "span_name": fn.__name__,
            "exec_time": None,
            "offset": round(
                0.0 if not SPAN.get() else t1 - RUNNING_TIME.get(),
                2,
            ),
            "code": inspect.getsource(fn),
            "inputs": inputs,
            "outputs": None,
            "errors": None,
            "child_spans": [],
        }
        token = SPAN.set(new_span)
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
            SPAN.get()["exec_time"] = round(exec_time, 2)
            SPAN.get()["outputs"] = None if result is None else result
            # ToDo: ensure there is a global log set upon the first trace,
            #  and removed on the last
            trace = SPAN.get()
            if prune_empty:
                trace = _prune_dict(trace)
            unify.add_log_entries(trace=trace, overwrite=True)
            if token.old_value is token.MISSING:
                SPAN.reset(token)
            else:
                SPAN.reset(token)
                SPAN.get()["child_spans"].append(new_span)
            if log_token:
                ACTIVE_LOG.set([])

    async def async_wrapped(*args, **kwargs):
        t1 = time.perf_counter()
        if not SPAN.get():
            RUNNING_TIME.set(t1)
        signature = inspect.signature(fn)
        bound_args = signature.bind(*args, **kwargs)
        bound_args.apply_defaults()
        inputs = bound_args.arguments
        new_span = {
            "id": str(uuid.uuid4()),
            "parent_span_id": (None if not SPAN.get() else SPAN.get()["id"]),
            "span_name": fn.__name__,
            "exec_time": None,
            "offset": round(
                0.0 if not SPAN.get() else t1 - RUNNING_TIME.get(),
                2,
            ),
            "inputs": inputs,
            "outputs": None,
            "errors": None,
            "child_spans": [],
        }
        token = SPAN.set(new_span)
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
            SPAN.get()["exec_time"] = round(exec_time, 2)
            SPAN.get()["outputs"] = None if result is None else result
            if token.old_value is token.MISSING:
                if ACTIVE_LOG.get():
                    trace = SPAN.get()
                    if prune_empty:
                        trace = _prune_dict(trace)
                    unify.add_log_entries(trace=trace, overwrite=True)
                else:
                    unify.log(trace=SPAN.get())
                SPAN.reset(token)
            else:
                SPAN.reset(token)
                SPAN.get()["child_spans"].append(new_span)

    return wrapped if not inspect.iscoroutinefunction(fn) else async_wrapped
