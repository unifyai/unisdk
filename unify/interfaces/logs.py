from __future__ import annotations

import time
import uuid
from typing import Any, Set, Dict, Callable, List, Optional, Tuple, Union
from datetime import datetime
from datetime import UTC
import ast
from functools import wraps
import textwrap


from ..utils.helpers import _validate_api_key, _prune_dict, _make_json_serializable
from .utils.logs import _handle_special_types, log as unify_log
from .utils.compositions import *


# Context Handlers #
# -----------------#


# noinspection PyShadowingBuiltins
class Log:
    def __init__(
        self,
        *,
        id: int = None,
        ts: Optional[datetime] = None,
        project: Optional[str] = None,
        context: Optional[str] = None,
        api_key: Optional[str] = None,
        params: Dict[str, Tuple[str, Any]] = None,
        **entries,
    ):
        self._id = id
        self._ts = ts
        self._project = project
        self._context = context
        self._entries = entries
        self._params = params
        self._api_key = _validate_api_key(api_key)

    # Setters

    def set_id(self, id: int) -> None:
        self._id = id

    # Properties

    @property
    def context(self) -> Optional[str]:
        return self._context

    @property
    def id(self) -> int:
        return self._id

    @property
    def ts(self) -> Optional[datetime]:
        return self._ts

    @property
    def entries(self) -> Dict[str, Any]:
        return self._entries

    @property
    def params(self) -> Dict[str, Tuple[str, Any]]:
        return self._params

    # Dunders

    def __eq__(self, other: Union[dict, Log]) -> bool:
        if isinstance(other, dict):
            other = Log(id=other["id"], **other["entries"])
        if self._id is not None and other._id is not None:
            return self._id == other._id
        return self.to_json() == other.to_json()

    def __len__(self):
        return len(self._entries) + len(self._params)

    def __repr__(self) -> str:
        return f"Log(id={self._id})"

    # Public

    def download(self):
        log = get_log_by_id(id=self._id, api_key=self._api_key)
        self._params = log._params
        self._entries = log._entries

    def add_entries(self, **entries) -> None:
        add_log_entries(logs=self._id, api_key=self._api_key, **entries)
        self._entries = {**self._entries, **entries}

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
            "ts": self._ts,
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
        self._log_token = ACTIVE_LOG.set(ACTIVE_LOG.get() + [lg])
        self._active_log_set = False
        self._id = lg.id
        self._ts = lg.ts

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.download()
        ACTIVE_LOG.reset(self._log_token)


class ColumnContext:
    def __init__(self, context: str):
        self._col_context = context

    def __enter__(self):
        self._col_context_token = COLUMN_CONTEXT.set(
            os.path.join(COLUMN_CONTEXT.get(), self._col_context),
        )

    def __exit__(self, *args, **kwargs):
        COLUMN_CONTEXT.reset(self._col_context_token)


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
    def __init__(self, name: Optional[Union[str, int]] = None, overwrite: bool = False):
        latest_exp_name = get_experiment_name(-1)
        if latest_exp_name is None:
            self._name = name if name is not None else "0"
            self._overwrite = overwrite
            return
        if isinstance(name, int):
            self._name = get_experiment_name(name)
        elif name is None:
            self._name = str(int(get_experiment_version(latest_exp_name)) + 1)
        else:
            self._name = str(name)
        self._overwrite = overwrite

    def __enter__(self):
        if self._overwrite:
            logs = get_logs(filter=f"experiment=='{self._name}'")
            delete_logs(logs=logs)
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


def traced(
    fn: callable = None,
    *,
    prune_empty: bool = True,
    span_type: str = "function",
    name: Optional[str] = None,
    trace_contexts: Optional[List[str]] = None,
):
    if fn is None:
        return lambda f: traced(
            f,
            prune_empty=prune_empty,
            span_type=span_type,
            trace_contexts=trace_contexts,
        )

    def wrapped(*args, **kwargs):
        log_token = None if ACTIVE_LOG.get() else ACTIVE_LOG.set([unify.log()])
        t1 = time.perf_counter()
        ts = datetime.now(UTC).isoformat()
        if not SPAN.get():
            RUNNING_TIME.set(t1)
        signature = inspect.signature(fn)
        bound_args = signature.bind(*args, **kwargs)
        bound_args.apply_defaults()
        inputs = bound_args.arguments
        inputs = inputs["kw"] if span_type == "llm-cached" else inputs
        inputs = _make_json_serializable(inputs)
        lines, start_line = inspect.getsourcelines(fn)
        code = "".join(lines)
        new_span = {
            "id": str(uuid.uuid4()),
            "type": span_type,
            "parent_span_id": (None if not SPAN.get() else SPAN.get()["id"]),
            "span_name": fn.__name__ if name is None else name,
            "exec_time": None,
            "timestamp": ts,
            "offset": round(
                0.0 if not SPAN.get() else t1 - RUNNING_TIME.get(),
                2,
            ),
            "cost": 0.0,
            "cost_inc_cache": 0.0,
            "code": f"```python\n{code}\n```",
            "code_fpath": inspect.getsourcefile(fn),
            "code_start_line": start_line,
            "inputs": inputs,
            "outputs": None,
            "errors": None,
            "child_spans": [],
        }
        if inspect.ismethod(fn) and hasattr(fn.__self__, "endpoint"):
            new_span["endpoint"] = fn.__self__.endpoint
        token = SPAN.set(new_span)
        result = None
        try:
            result = fn(*args, **kwargs)
            return result
        except Exception as e:
            new_span["errors"] = str(e)
            raise e
        finally:
            if result is None:
                outputs = None
                if SPAN.get()["type"] == "llm-cached":
                    # tried to load cache but nothing found,
                    # do not add this failed cache load to trace
                    if token.old_value is token.MISSING:
                        SPAN.reset(token)
                    else:
                        SPAN.reset(token)
                    if log_token:
                        ACTIVE_LOG.set([])
                    return
            else:
                outputs = _make_json_serializable(result)
            t2 = time.perf_counter()
            exec_time = t2 - t1
            SPAN.get()["exec_time"] = exec_time
            SPAN.get()["outputs"] = outputs
            if SPAN.get()["type"] == "llm":
                SPAN.get()["cost"] = outputs["usage"]["cost"]
            if SPAN.get()["type"] in ("llm", "llm-cached"):
                SPAN.get()["cost_inc_cache"] = outputs["usage"]["cost"]
            # ToDo: ensure there is a global log set upon the first trace,
            #  and removed on the last
            trace = SPAN.get()
            if prune_empty:
                trace = _prune_dict(trace)
            unify.add_log_entries(
                trace=trace,
                overwrite=True,
                # mutable=SPAN.get()["parent_span_id"] is not None,
            )
            SPAN.reset(token)
            if token.old_value is not token.MISSING:
                SPAN.get()["child_spans"].append(new_span)
                SPAN.get()["cost"] += new_span["cost"]
                SPAN.get()["cost_inc_cache"] += new_span["cost_inc_cache"]
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
            "type": span_type,
            "parent_span_id": (None if not SPAN.get() else SPAN.get()["id"]),
            "span_name": fn.__name__ if name is None else name,
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
            SPAN.get()["exec_time"] = exec_time
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


class LogTransformer(ast.NodeTransformer):
    def __init__(self):
        super().__init__()
        self.param_names = []
        self.assigned_names = set()
        self._in_function = False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._in_function = True
        self.param_names = [
            arg.arg for arg in node.args.args if not arg.arg.startswith("_")
        ]

        for arg in node.args.kwonlyargs:
            if not arg.arg.startswith("_"):
                self.param_names.append(arg.arg)

        node = self.generic_visit(node)
        self._in_function = False
        self.param_names = []
        self.assigned_names = set()
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._in_function = True
        self.param_names = [
            arg.arg for arg in node.args.args if not arg.arg.startswith("_")
        ]
        node = self.generic_visit(node)
        self._in_function = False
        self.param_names = []
        self.assigned_names = set()
        return node

    def visit_Assign(self, node: ast.Assign):
        if self._in_function:
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    self.assigned_names.add(target.id)
        return node

    def visit_Return(self, node: ast.Return):
        if not self._in_function:
            return node

        log_keywords = []
        for p in self.param_names:
            log_keywords.append(
                ast.keyword(arg=p, value=ast.Name(id=p, ctx=ast.Load())),
            )

        for var_name in sorted(self.assigned_names):
            log_keywords.append(
                ast.keyword(arg=var_name, value=ast.Name(id=var_name, ctx=ast.Load())),
            )

        return_value = (
            node.value if node.value is not None else ast.Constant(value=None)
        )

        log_call = ast.Expr(
            value=ast.Call(
                func=ast.Name(id="unify_log", ctx=ast.Load()),
                args=[],
                keywords=log_keywords,
            ),
        )

        return [log_call, ast.Return(value=return_value)]


def log_decorator(func):
    """
    Decorator that rewrites the function's AST so that it logs non-underscore
    parameters, and assigned variables.
    """
    # 1) Parse the source to an AST
    source = textwrap.dedent(inspect.getsource(func))

    # Remove the decorator line if present
    source_lines = source.split("\n")
    if source_lines[0].strip().startswith("@"):
        source = "\n".join(source_lines[1:])

    mod = ast.parse(source)

    # 2) Transform the AST
    transformer = LogTransformer()
    mod = transformer.visit(mod)
    ast.fix_missing_locations(mod)

    # 3) Compile the new AST
    code = compile(mod, filename="<ast>", mode="exec")

    # 4) Create a dict for the module namespace in which we'll execute
    func_globals = func.__globals__.copy()
    func_globals["unify_log"] = unify_log

    # 5) Execute the compiled module code in that namespace
    exec(code, func_globals)
    transformed_func = func_globals[func.__name__]

    transformed_func.__name__ = func.__name__
    transformed_func.__doc__ = func.__doc__
    transformed_func.__module__ = func.__module__
    transformed_func.__annotations__ = func.__annotations__
    return transformed_func


def log_inputs(func: Callable) -> Callable:
    """
    Decorator that logs function inputs, and intermediate values.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if inspect.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                transformed = log_decorator(func)
                return await transformed(*args, **kwargs)

            return async_wrapper(*args, **kwargs)
        transformed = log_decorator(func)
        return transformed(*args, **kwargs)

    return wrapper


# Expose the decorator at the module level
__all__ = ["Log", "ColumnContext", "Entries", "Params", "Experiment", "log"]
