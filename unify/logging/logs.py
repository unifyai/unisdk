from __future__ import annotations

import ast
import copy
import functools
import inspect
import logging
import textwrap
import time
import traceback
import uuid
from datetime import datetime, timezone
from types import MethodType, ModuleType
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from ..utils.helpers import _make_json_serializable, _prune_dict, _validate_api_key
from .utils.compositions import *
from .utils.logs import (
    _get_trace_logger,
    _handle_special_types,
    _reset_active_trace_parameters,
    _set_active_trace_parameters,
    get_trace_context,
    initialize_trace_logger,
)
from .utils.logs import log as unify_log

_traced_logger = logging.getLogger("unify_tracer")
_traced_logger_enabled = os.getenv("UNIFY_TRACED_DEBUG", "false").lower() in (
    "true",
    "1",
)
_traced_logger.setLevel(logging.DEBUG if _traced_logger_enabled else logging.ERROR)

# Context Handlers #
# -----------------#


def _validate_mode(mode: str) -> None:
    assert mode in (
        "both",
        "read",
        "write",
    ), f"mode must be one of 'read', 'write', or 'both', but found {mode}"


def _validate_mode_nesting(parent_mode: str, child_mode: str) -> None:
    if not (parent_mode in ("both", child_mode)):
        raise Exception(
            f"Cannot nest context with mode '{child_mode}' under parent with mode '{parent_mode}'",
        )


# noinspection PyShadowingBuiltins
class Log:
    def __init__(
        self,
        *,
        id: int = None,
        _future=None,
        ts: Optional[datetime] = None,
        project: Optional[str] = None,
        context: Optional[str] = None,
        api_key: Optional[str] = None,
        params: Dict[str, Tuple[str, Any]] = None,
        **entries,
    ):
        self._id = id
        self._future = _future
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
        if self._id is None and self._future is not None and self._future.done():
            self._id = self._future.result()
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
        # If id is not yet resolved, wait for the future
        if self._id is None and self._future is not None:
            self._id = self._future.result(timeout=5)
        log = get_log_by_id(id=self._id, api_key=self._api_key)
        self._params = log._params
        self._entries = log._entries

    def add_entries(self, **entries) -> None:
        add_log_entries(
            logs=self._id,
            context=self._context,
            api_key=self._api_key,
            **entries,
        )
        self._entries = {**self._entries, **entries}

    def update_entries(self, **entries) -> None:
        update_logs(
            logs=self._id,
            api_key=self._api_key,
            context=self._context,
            entries=entries,
            overwrite=True,
        )
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
        if self._id is None and self._future is not None:
            self.download()
        ACTIVE_LOG.reset(self._log_token)


class LogGroup:
    def __init__(self, field, value: Union[List[unify.Log], "LogGroup"] = None):
        self.field = field
        self.value = value

    def __repr__(self):
        return f"LogGroup(field={self.field}, value={self.value})"


def _join_path(base_path: str, context: str) -> str:
    return os.path.join(
        base_path,
        os.path.normpath(context),
    ).replace("\\", "/")


def set_context(context: str, mode: str = "both", overwrite: bool = False):
    global MODE, MODE_TOKEN, CONTEXT_READ_TOKEN, CONTEXT_WRITE_TOKEN
    MODE = mode
    _validate_mode_nesting(CONTEXT_MODE.get(), mode)
    MODE_TOKEN = CONTEXT_MODE.set(mode)

    if overwrite and context in unify.get_contexts():
        if mode == "read":
            raise Exception(f"Cannot overwrite logs in read mode.")
        unify.delete_context(context)
    if context not in unify.get_contexts():
        unify.create_context(context)

    if mode in ("both", "write"):
        CONTEXT_WRITE_TOKEN = CONTEXT_WRITE.set(
            _join_path(CONTEXT_WRITE.get(), context),
        )
    if mode in ("both", "read"):
        CONTEXT_READ_TOKEN = CONTEXT_READ.set(
            _join_path(CONTEXT_READ.get(), context),
        )


def unset_context():
    global MODE, MODE_TOKEN, CONTEXT_READ_TOKEN, CONTEXT_WRITE_TOKEN
    if MODE in ("both", "write"):
        CONTEXT_WRITE.reset(CONTEXT_WRITE_TOKEN)
    if MODE in ("both", "read"):
        CONTEXT_READ.reset(CONTEXT_READ_TOKEN)

    CONTEXT_MODE.reset(MODE_TOKEN)


def get_active_context():
    return {"read": CONTEXT_READ.get(), "write": CONTEXT_WRITE.get()}


class Context:
    def __init__(
        self,
        context: str,
        mode: str = "both",
        overwrite: bool = False,
        is_versioned: bool = True,
    ):
        self._context = context
        _validate_mode(mode)
        self._mode = mode
        self._overwrite = overwrite
        self._is_versioned = is_versioned

    def __enter__(self):
        _validate_mode_nesting(CONTEXT_MODE.get(), self._mode)
        self._mode_token = CONTEXT_MODE.set(self._mode)

        if self._mode in ("both", "write"):
            self._context_write_token = CONTEXT_WRITE.set(
                _join_path(CONTEXT_WRITE.get(), self._context),
            )
        if self._mode in ("both", "read"):
            self._context_read_token = CONTEXT_READ.set(
                _join_path(CONTEXT_READ.get(), self._context),
            )

        if self._overwrite and self._context in unify.get_contexts():
            if self._mode == "read":
                raise Exception(f"Cannot overwrite logs in read mode.")

            unify.delete_context(self._context)
            unify.create_context(self._context, is_versioned=self._is_versioned)

    def __exit__(self, *args, **kwargs):
        if self._mode in ("both", "write"):
            CONTEXT_WRITE.reset(self._context_write_token)
        if self._mode in ("both", "read"):
            CONTEXT_READ.reset(self._context_read_token)

        CONTEXT_MODE.reset(self._mode_token)


class ColumnContext:
    def _join_path(self, base_path: str, context: str) -> str:
        return os.path.join(
            base_path,
            os.path.normpath(context),
            "",
        ).replace("\\", "/")

    def __init__(self, context: str, mode: str = "both", overwrite: bool = False):
        self._col_context = context
        _validate_mode(mode)
        self._mode = mode
        self._overwrite = overwrite

    def __enter__(self):
        _validate_mode_nesting(COLUMN_CONTEXT_MODE.get(), self._mode)
        self._mode_token = COLUMN_CONTEXT_MODE.set(self._mode)

        if self._mode in ("both", "write"):
            self._context_write_token = COLUMN_CONTEXT_WRITE.set(
                self._join_path(COLUMN_CONTEXT_WRITE.get(), self._col_context),
            )
        if self._mode in ("both", "read"):
            self._context_read_token = COLUMN_CONTEXT_READ.set(
                self._join_path(COLUMN_CONTEXT_READ.get(), self._col_context),
            )

        if self._overwrite:
            if self._mode == "read":
                raise Exception(f"Cannot overwrite logs in read mode.")

            logs = unify.get_logs(return_ids_only=True)
            if len(logs) > 0:
                unify.delete_logs(logs=logs)

    def __exit__(self, *args, **kwargs):
        if self._mode in ("both", "write"):
            COLUMN_CONTEXT_WRITE.reset(self._context_write_token)
        if self._mode in ("both", "read"):
            COLUMN_CONTEXT_READ.reset(self._context_read_token)
        COLUMN_CONTEXT_MODE.reset(self._mode_token)


class Entries:
    def __init__(self, mode: str = "both", overwrite: bool = False, **entries):
        self._entries = _handle_special_types(entries)
        _validate_mode(mode)
        self._mode = mode
        self._overwrite = overwrite

    def __enter__(self):
        _validate_mode_nesting(ACTIVE_ENTRIES_MODE.get(), self._mode)
        self._mode_token = ACTIVE_ENTRIES_MODE.set(self._mode)
        if self._mode in ("both", "write"):
            self._entries_token = ACTIVE_ENTRIES_WRITE.set(
                {**ACTIVE_ENTRIES_WRITE.get(), **self._entries},
            )
            self._nest_token = ENTRIES_NEST_LEVEL.set(
                ENTRIES_NEST_LEVEL.get() + 1,
            )

        if self._mode in ("both", "read"):
            self._entries_read_token = ACTIVE_ENTRIES_READ.set(
                {**ACTIVE_ENTRIES_READ.get(), **self._entries},
            )

        if self._overwrite:
            if self._mode == "read":
                raise Exception(f"Cannot overwrite logs in read mode.")

            logs = unify.get_logs(return_ids_only=True)
            if len(logs) > 0:
                unify.delete_logs(logs=logs)

    def __exit__(self, *args, **kwargs):
        if self._mode in ("both", "write"):
            ACTIVE_ENTRIES_WRITE.reset(self._entries_token)
            ENTRIES_NEST_LEVEL.reset(self._nest_token)
            if ENTRIES_NEST_LEVEL.get() == 0:
                LOGGED.set({})

        if self._mode in ("both", "read"):
            ACTIVE_ENTRIES_READ.reset(self._entries_read_token)

        ACTIVE_ENTRIES_MODE.reset(self._mode_token)


class Params:
    def __init__(self, mode: str = "both", overwrite: bool = False, **params):
        self._params = _handle_special_types(params)
        _validate_mode(mode)
        self._mode = mode
        self._overwrite = overwrite

    def __enter__(self):
        _validate_mode_nesting(ACTIVE_PARAMS_MODE.get(), self._mode)
        self._mode_token = ACTIVE_PARAMS_MODE.set(self._mode)
        if self._mode in ("both", "write"):
            self._params_token = ACTIVE_PARAMS_WRITE.set(
                {**ACTIVE_PARAMS_WRITE.get(), **self._params},
            )
            self._nest_token = PARAMS_NEST_LEVEL.set(
                PARAMS_NEST_LEVEL.get() + 1,
            )

        if self._mode in ("both", "read"):
            self._params_read_token = ACTIVE_PARAMS_READ.set(
                {**ACTIVE_PARAMS_READ.get(), **self._params},
            )

        if self._overwrite:
            if self._mode == "read":
                raise Exception(f"Cannot overwrite logs in read mode.")

            logs = unify.get_logs(return_ids_only=True)
            if len(logs) > 0:
                unify.delete_logs(logs=logs)

    def __exit__(self, *args, **kwargs):
        ACTIVE_PARAMS_MODE.reset(self._mode_token)

        if self._mode in ("both", "write"):
            ACTIVE_PARAMS_WRITE.reset(self._params_token)
            PARAMS_NEST_LEVEL.reset(self._nest_token)
            if PARAMS_NEST_LEVEL.get() == 0:
                LOGGED.set({})

        if self._mode in ("both", "read"):
            ACTIVE_PARAMS_READ.reset(self._params_read_token)


class Experiment:
    def __init__(
        self,
        name: Optional[Union[str, int]] = None,
        overwrite: bool = False,
        mode: str = "both",
    ):
        _validate_mode(mode)
        self._mode = mode

        latest_exp_name = get_experiment_name(-1)
        if latest_exp_name is None:
            self._name = name if name is not None else "exp0"
            self._overwrite = overwrite
            return
        if isinstance(name, int):
            self._name = f"exp{get_experiment_name(name)}"
        elif name is None:
            self._name = f"exp{int(get_experiment_version(latest_exp_name)) + 1}"
        else:
            self._name = str(name)
        self._overwrite = overwrite

    def __enter__(self):
        _validate_mode_nesting(ACTIVE_PARAMS_MODE.get(), self._mode)
        self._mode_token = ACTIVE_PARAMS_MODE.set(self._mode)

        if self._mode in ("both", "write"):
            self._params_token_write = ACTIVE_PARAMS_WRITE.set(
                {**ACTIVE_PARAMS_WRITE.get(), **{"experiment": self._name}},
            )
            self._nest_token = PARAMS_NEST_LEVEL.set(
                PARAMS_NEST_LEVEL.get() + 1,
            )
        if self._mode in ("both", "read"):
            self._params_read_token = ACTIVE_PARAMS_READ.set(
                {**ACTIVE_PARAMS_READ.get(), **{"experiment": self._name}},
            )

        if self._overwrite:
            if self._mode == "read":
                raise Exception(f"Cannot overwrite logs in read mode.")

            logs = unify.get_logs(return_ids_only=True)
            if len(logs) > 0:
                unify.delete_logs(logs=logs)

    def __exit__(self, *args, **kwargs):
        ACTIVE_PARAMS_MODE.reset(self._mode_token)
        if self._mode in ("both", "write"):
            ACTIVE_PARAMS_WRITE.reset(self._params_token_write)
            PARAMS_NEST_LEVEL.reset(self._nest_token)
            if PARAMS_NEST_LEVEL.get() == 0:
                LOGGED.set({})
        if self._mode in ("both", "read"):
            ACTIVE_PARAMS_READ.reset(self._params_read_token)


# Tracing #
# --------#


class TracerCallCollector(ast.NodeVisitor):
    def __init__(self, main_function_name):
        self.main_function_name = main_function_name
        self.call_names = set()
        self.local_function_names = set()

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        self.local_function_names.add(node.name)
        return node

    def visit_AsyncFunctionDef(self, node):
        self.generic_visit(node)
        self.local_function_names.add(node.name)
        return node

    def visit_Call(self, node):
        self.generic_visit(node)

        if isinstance(node.func, ast.Name):
            self.call_names.add(node.func.id)

        if isinstance(node.func, ast.Attribute):
            self.call_names.add(node.func.attr)

    def get_external_call_names(self):
        return self.call_names - self.local_function_names

    def get_local_function_names(self):
        return self.local_function_names - set([self.main_function_name])


class TracerCallTransformer(ast.NodeTransformer):
    def __init__(self, local_defined_functions_names, non_local_call_names):
        self.local_defined_functions_names = local_defined_functions_names
        self.non_local_call_names = non_local_call_names

    def visit_FunctionDef(self, node):
        if node.name in self.local_defined_functions_names:
            node.decorator_list.append(
                ast.Call(
                    func=ast.Name(id="traced", ctx=ast.Load()),
                    args=[],
                    keywords=[],
                ),
            )
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node):
        if node.name in self.local_defined_functions_names:
            node.decorator_list.append(
                ast.Call(
                    func=ast.Name(id="traced", ctx=ast.Load()),
                    args=[],
                    keywords=[],
                ),
            )
        self.generic_visit(node)
        return node

    def visit_Call(self, node):
        node = self.generic_visit(node)

        if (
            isinstance(node.func, ast.Name)
            and node.func.id in self.non_local_call_names
        ):
            tracer = ast.Call(
                func=ast.Name(id="traced", ctx=ast.Load()),
                args=[ast.Name(id=node.func.id, ctx=ast.Load())],
                keywords=[],
            )
            return ast.copy_location(
                ast.Call(func=tracer, args=node.args, keywords=node.keywords),
                node,
            )

        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in self.non_local_call_names
        ):
            tracer = ast.Call(
                func=ast.Name(id="traced", ctx=ast.Load()),
                args=[node.func],
                keywords=[],
            )
            return ast.copy_location(
                ast.Call(func=tracer, args=node.args, keywords=node.keywords),
                node,
            )

        return node


class _Traced:
    def __init__(self, fn, args, kwargs, span_type, name, prune_empty):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.span_type = span_type
        self.name = name
        self.prune_empty = prune_empty
        self.result = None

    def __enter__(self):
        self.log_token = (
            None
            if ACTIVE_TRACE_LOG.get()
            else ACTIVE_TRACE_LOG.set([unify.log(context=get_trace_context())])
        )
        self.new_span, self.exec_start_time, self.local_token, self.global_token = (
            _create_span(
                self.fn,
                self.args,
                self.kwargs,
                self.span_type,
                self.name,
            )
        )
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        exec_time = time.perf_counter() - self.exec_start_time
        if exc_type:
            self.new_span["errors"] = traceback.format_exc()
        outputs = (
            _make_json_serializable(self.result) if self.result is not None else None
        )
        _finalize_span(
            self.new_span,
            self.local_token,
            outputs,
            exec_time,
            self.prune_empty,
            self.global_token,
        )
        if self.log_token:
            ACTIVE_TRACE_LOG.set([])


class Traced:
    def __init__(self, name, *, globals_filter=None):
        self.name = name
        self.globals_filter = globals_filter or self._default_globals_filter
        initialize_trace_logger()

    def _default_globals_filter(self, name, obj):
        return not (
            name.startswith("__") or name.endswith("__") or inspect.ismodule(obj)
        )

    def __enter__(self):
        self.frame = inspect.currentframe().f_back

        try:
            self.code = inspect.getsource(self.frame.f_code)
            self.code_fpath = inspect.getsourcefile(self.frame.f_code)
            self.start_linenumber = inspect.getsourcelines(self.frame.f_code)[1]
        except OSError:
            self.code = ""
            self.code_fpath = ""
            self.start_linenumber = 0

        self.runtime_lineno = self.frame.f_lineno

        self.log_token = (
            None
            if ACTIVE_TRACE_LOG.get()
            else ACTIVE_TRACE_LOG.set([unify.log(context=get_trace_context())])
        )

        self.used_vars = self._extract_read_vars()
        self.inputs = {}

        def _deepcopy_or_original(v):
            # If deepcopy fails, we just capture the original value
            # This will fail to capture output state if the variable was modified in the function
            try:
                return copy.deepcopy(v)
            except Exception as e:
                return v

        for k, v in self.frame.f_globals.items():
            if k in self.used_vars and self.globals_filter(k, v):
                self.inputs[k] = _deepcopy_or_original(v)

        for k, v in self.frame.f_locals.items():
            if k in self.used_vars:
                self.inputs[k] = _deepcopy_or_original(v)

        self.exec_start_time = time.perf_counter()
        ts = datetime.now(timezone.utc).isoformat()
        if not SPAN.get():
            RUNNING_TIME.set(self.exec_start_time)

        new_span = {
            "id": str(uuid.uuid4()),
            "type": "context",
            "parent_span_id": (None if not SPAN.get() else SPAN.get()["id"]),
            "span_name": self.name,
            "exec_time": None,
            "timestamp": ts,
            "offset": round(
                0.0 if not SPAN.get() else self.exec_start_time - RUNNING_TIME.get(),
                2,
            ),
            "llm_usage": None,
            "llm_usage_inc_cache": None,
            "code": f"```python\n{self.code}\n```",
            "code_fpath": self.code_fpath,
            "code_start_line": self.runtime_lineno,
            "inputs": _make_json_serializable(self.inputs) if self.inputs else None,
            "outputs": None,
            "errors": None,
            "child_spans": [],
            "completed": False,
        }

        if not GLOBAL_SPAN.get():
            self.global_token = GLOBAL_SPAN.set(new_span)
            self.local_token = SPAN.set(GLOBAL_SPAN.get())
        else:
            self.global_token = None
            SPAN.get()["child_spans"].append(new_span)
            self.local_token = SPAN.set(new_span)

        _get_trace_logger().update_trace(
            ACTIVE_TRACE_LOG.get()[0],
            copy.deepcopy(GLOBAL_SPAN.get()),
        )
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        SPAN.get()["exec_time"] = time.perf_counter() - self.exec_start_time

        # Outputs contains variables that are:
        # - Created in the function
        # - Inputs that have been modified
        outputs = {}
        for k, v in self.frame.f_globals.items():
            if k in self.inputs:
                if self.inputs[k] != v:
                    outputs[k] = v

        for k, v in self.frame.f_locals.items():
            if k in self.inputs:
                if self.inputs[k] != v:
                    outputs[k] = v
            elif k in self.used_vars:
                outputs[k] = v

        SPAN.get()["outputs"] = _make_json_serializable(outputs) if outputs else None
        SPAN.get()["completed"] = True
        if exc_tb:
            SPAN.get()["errors"] = traceback.format_exc()

        SPAN.reset(self.local_token)
        _get_trace_logger().update_trace(
            ACTIVE_TRACE_LOG.get()[0],
            copy.deepcopy(GLOBAL_SPAN.get()),
        )
        if self.global_token:
            GLOBAL_SPAN.reset(self.global_token)
        if self.log_token:
            ACTIVE_TRACE_LOG.set([])

    class _VarReadVisitor(ast.NodeVisitor):
        def __init__(self):
            self.read_vars = set()

        def visit_Name(self, node):
            self.read_vars.add(node.id)

        def visit_withitem(self, node):
            pass

    class _WithBlockFinder(ast.NodeVisitor):
        def __init__(self, lineno):
            self.lineno = lineno
            self.target_node = None

        def visit_With(self, node):
            if node.lineno <= self.lineno <= node.end_lineno:
                self.target_node = node

    def _extract_read_vars(self):
        if not self.code:
            return set()

        tree = ast.parse(textwrap.dedent(self.code))

        finder = self._WithBlockFinder(self.runtime_lineno - self.start_linenumber + 1)
        finder.visit(tree)

        if not finder.target_node:
            return set()

        reader = self._VarReadVisitor()
        reader.visit(finder.target_node)

        return reader.read_vars


def _print_tree_source_with_lineno(fn_name, tree):
    source_unparsed = "\n".join(
        f"{i+1}: {line}" for i, line in enumerate(ast.unparse(tree).split("\n"))
    )
    _traced_logger.debug(f"AST[{fn_name}]:\n{source_unparsed}")


def _nested_add(a, b):
    if a is None and isinstance(b, dict):
        a = {k: None if isinstance(v, dict) else 0 for k, v in b.items()}
    elif b is None and isinstance(a, dict):
        b = {k: None if isinstance(v, dict) else 0 for k, v in a.items()}
    if isinstance(a, dict) and isinstance(b, dict):
        return {k: _nested_add(a[k], b[k]) for k in a if k in b}
    elif a is None and b is None:
        return None
    elif a is None:
        return b
    elif b is None:
        return a
    return a + b


def _create_span(fn, args, kwargs, span_type, name):
    exec_start_time = time.perf_counter()
    ts = datetime.now(timezone.utc).isoformat()
    if not SPAN.get():
        RUNNING_TIME.set(exec_start_time)
    signature = inspect.signature(fn)
    bound_args = signature.bind(*args, **kwargs)
    bound_args.apply_defaults()
    inputs = bound_args.arguments
    inputs = inputs["kw"] if span_type == "llm-cached" else inputs
    inputs = _make_json_serializable(inputs)
    try:
        lines, start_line = inspect.getsourcelines(fn)
        code = textwrap.dedent("".join(lines))
    except:
        lines, start_line = None, None
        try:
            code = textwrap.dedent(inspect.getsource(fn))
        except:
            code = None
    name_w_sub = name
    if name_w_sub is not None:
        for k, v in inputs.items():
            substr = "{" + k + "}"
            if substr in name_w_sub:
                name_w_sub = name_w_sub.replace(substr, str(v))

    try:
        code_fpath = inspect.getsourcefile(fn)
    except Exception as e:
        code_fpath = None

    new_span = {
        "id": str(uuid.uuid4()),
        "type": span_type,
        "parent_span_id": (None if not SPAN.get() else SPAN.get()["id"]),
        "span_name": fn.__name__ if name_w_sub is None else name_w_sub,
        "exec_time": None,
        "timestamp": ts,
        "offset": round(
            0.0 if not SPAN.get() else exec_start_time - RUNNING_TIME.get(),
            2,
        ),
        "llm_usage": None,
        "llm_usage_inc_cache": None,
        "code": f"```python\n{code}\n```",
        "code_fpath": code_fpath,
        "code_start_line": start_line,
        "inputs": inputs,
        "outputs": None,
        "errors": None,
        "child_spans": [],
        "completed": False,
    }
    if inspect.ismethod(fn) and hasattr(fn.__self__, "endpoint"):
        new_span["endpoint"] = fn.__self__.endpoint
    if not GLOBAL_SPAN.get():
        global_token = GLOBAL_SPAN.set(new_span)
        local_token = SPAN.set(GLOBAL_SPAN.get())
    else:
        global_token = None
        SPAN.get()["child_spans"].append(new_span)
        local_token = SPAN.set(new_span)
    _get_trace_logger().update_trace(
        ACTIVE_TRACE_LOG.get()[0],
        copy.deepcopy(GLOBAL_SPAN.get()),
    )
    return new_span, exec_start_time, local_token, global_token


def _finalize_span(
    new_span,
    local_token,
    outputs,
    exec_time,
    prune_empty,
    global_token,
):
    SPAN.get()["exec_time"] = exec_time
    SPAN.get()["outputs"] = outputs
    SPAN.get()["completed"] = True
    if SPAN.get()["type"] == "llm" and outputs is not None:
        SPAN.get()["llm_usage"] = outputs["usage"]
    if SPAN.get()["type"] in ("llm", "llm-cached") and outputs is not None:
        SPAN.get()["llm_usage_inc_cache"] = outputs["usage"]
    trace = SPAN.get()
    if prune_empty:
        trace = _prune_dict(trace)
        SPAN.set(trace)
        if global_token:
            GLOBAL_SPAN.set(trace)
    SPAN.reset(local_token)
    if local_token.old_value is not local_token.MISSING:
        SPAN.get()["llm_usage"] = _nested_add(
            SPAN.get()["llm_usage"],
            new_span["llm_usage"],
        )
        SPAN.get()["llm_usage_inc_cache"] = _nested_add(
            SPAN.get()["llm_usage_inc_cache"],
            new_span["llm_usage_inc_cache"],
        )
    _get_trace_logger().update_trace(
        ACTIVE_TRACE_LOG.get()[0],
        copy.deepcopy(GLOBAL_SPAN.get()),
    )
    if global_token:
        GLOBAL_SPAN.reset(global_token)


def _default_trace_filter(obj, name):
    return not (name.startswith("__") and name.endswith("__"))


def _trace_class(cls, prune_empty, span_type, name, filter):
    _obj_filter = (
        lambda obj: inspect.isfunction(obj)
        or inspect.isclass(obj)
        or inspect.ismethod(obj)
    )
    for member_name, value in inspect.getmembers(cls, predicate=_obj_filter):
        if not filter(value, member_name):
            continue

        _name = f"{name if name is not None else cls.__name__}.{member_name}"
        try:
            setattr(
                cls,
                member_name,
                traced(value, prune_empty=prune_empty, span_type=span_type, name=_name),
            )
        except AttributeError:
            pass
    return cls


def _trace_instance(inst, prune_empty, span_type, name, filter):
    """
    Trace *only this instance* – the class itself is left untouched.
    Every callable attribute that passes `filter` is wrapped and rebound
    to the original instance so that `self` works exactly as before.
    """
    cls_name = type(inst).__name__
    obj_filter = lambda obj: callable(obj)

    for member_name, value in inspect.getmembers(inst, predicate=obj_filter):
        if not filter(value, member_name):
            continue

        span_name = f"{name if name is not None else cls_name}.{member_name}"

        # Use the class-level (unbound) function if it exists – cleaner `@wraps`
        unbound = getattr(type(inst), member_name, value)
        traced_fn = traced(
            unbound,
            prune_empty=prune_empty,
            span_type=span_type,
            name=span_name,
            filter=filter,
        )

        # Determine the original attribute type (regular, staticmethod, classmethod)
        try:
            original_attr = inspect.getattr_static(type(inst), member_name)
        except AttributeError:
            original_attr = None

        # Re-bind based on attribute type
        try:
            if isinstance(original_attr, staticmethod):
                # For staticmethods we do NOT bind to the instance – they behave like plain functions
                setattr(inst, member_name, traced_fn)
            elif isinstance(original_attr, classmethod):
                # For classmethods we bind to the *class*, not the instance
                setattr(inst, member_name, MethodType(traced_fn, type(inst)))
            else:
                # Regular instance methods get bound to the instance so that `self` is passed correctly
                setattr(inst, member_name, MethodType(traced_fn, inst))
        except AttributeError:
            pass

    return inst


def _trace_module(module, prune_empty, span_type, name, filter):
    _obj_filter = (
        lambda obj: inspect.isfunction(obj)
        or inspect.isclass(obj)
        or inspect.ismethod(obj)
    )
    for member_name, value in inspect.getmembers(module, predicate=_obj_filter):
        if not filter(value, member_name):
            continue

        _name = f"{name if name is not None else module.__name__}.{member_name}"
        try:
            setattr(
                module,
                member_name,
                traced(value, prune_empty=prune_empty, span_type=span_type, name=_name),
            )
        except AttributeError:
            pass
    return module


def _get_or_compile(func, compiled_ast):
    if hasattr(func, "__cached_tracer"):
        transformed_func = getattr(func, "__cached_tracer")
        _traced_logger.debug(f"Using cached tracer for {func.__name__}")
    else:
        is_bound = hasattr(func, "__self__") and func.__self__ is not None
        orig_fn = func.__func__ if is_bound else func
        instance = func.__self__ if is_bound else None
        global_ns = func.__globals__.copy()

        # TODO: This is a hack to get the original function's closure
        if orig_fn.__closure__:
            for var, cell in zip(orig_fn.__code__.co_freevars, orig_fn.__closure__):
                global_ns[var] = cell.cell_contents

        global_ns["traced"] = traced
        local_ns = {}
        _traced_logger.debug(f"Executing compiled AST for {func.__name__}")
        exec(compiled_ast, global_ns, local_ns)
        transformed_func = local_ns[orig_fn.__name__]
        if is_bound:
            transformed_func = MethodType(transformed_func, instance)
        try:
            setattr(func, "__cached_tracer", transformed_func)
        except:
            pass

    return transformed_func


def _trace_wrapper_factory(
    *,
    fn,
    fn_type,
    span_type,
    name,
    prune_empty,
    recursive,
    filter,
    depth,
    compiled_ast,
    skip_modules,
    skip_functions,
):

    is_coroutine = inspect.iscoroutinefunction(inspect.unwrap(fn)) or fn_type == "async"
    if is_coroutine and recursive:

        @functools.wraps(fn)
        async def async_wrapped(*args, **kwargs):
            token = _set_active_trace_parameters(
                prune_empty=prune_empty,
                span_type=span_type,
                name=name,
                filter=filter,
                fn_type=fn_type,
                recursive=recursive,
                depth=depth,
                skip_modules=skip_modules,
                skip_functions=skip_functions,
            )
            transformed_fn = _get_or_compile(fn, compiled_ast)
            with _Traced(fn, args, kwargs, span_type, name, prune_empty) as _t:
                result = await transformed_fn(*args, **kwargs)
                _t.result = result
                _reset_active_trace_parameters(token)
                return result

        return async_wrapped

    if is_coroutine and not recursive:

        @functools.wraps(fn)
        async def async_wrapped(*args, **kwargs):
            with _Traced(fn, args, kwargs, span_type, name, prune_empty) as _t:
                result = await fn(*args, **kwargs)
                _t.result = result
                return result

        return async_wrapped

    is_function = inspect.isfunction(fn) or inspect.ismethod(fn)
    if is_function and recursive:

        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            token = _set_active_trace_parameters(
                prune_empty=prune_empty,
                span_type=span_type,
                name=name,
                filter=filter,
                fn_type=fn_type,
                recursive=recursive,
                depth=depth,
                skip_modules=skip_modules,
                skip_functions=skip_functions,
            )
            transformed_fn = _get_or_compile(fn, compiled_ast)
            with _Traced(fn, args, kwargs, span_type, name, prune_empty) as _t:
                result = transformed_fn(*args, **kwargs)
                _t.result = result
                _reset_active_trace_parameters(token)
                return result

        return wrapped

    if is_function and not recursive:

        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            with _Traced(fn, args, kwargs, span_type, name, prune_empty) as _t:
                result = fn(*args, **kwargs)
                _t.result = result
                return result

        return wrapped

    raise TypeError(
        f"Unsupported object type, should be function, coroutine or method: {fn_type}",
    )


def _trace_function(
    fn,
    prune_empty,
    span_type,
    name,
    filter,
    fn_type,
    recursive,
    depth,
    skip_modules,
    skip_functions,
):
    _traced_logger.debug(f"Applying trace decorator to function {fn.__name__}")

    if not recursive or depth <= 0:
        return _trace_wrapper_factory(
            fn=fn,
            fn_type=fn_type,
            span_type=span_type,
            name=name,
            prune_empty=prune_empty,
            recursive=False,
            filter=filter,
            depth=0,
            compiled_ast=None,
            skip_modules=skip_modules,
            skip_functions=skip_functions,
        )

    try:
        source = inspect.getsource(fn)
        source = textwrap.dedent(source)
    except Exception as e:
        _traced_logger.warning(f"Error getting source for {fn.__name__}: {e}")
        # Fallback to non-recursive tracing
        return _trace_wrapper_factory(
            fn=fn,
            fn_type=fn_type,
            span_type=span_type,
            name=name,
            prune_empty=prune_empty,
            recursive=False,
            filter=filter,
            depth=depth,
            compiled_ast=None,
            skip_modules=skip_modules,
            skip_functions=skip_functions,
        )

    parsed_ast = ast.parse(source)
    func_def = parsed_ast.body[0]
    if not isinstance(func_def, (ast.FunctionDef, ast.AsyncFunctionDef)):
        # Fallback to non-recursive tracing
        return _trace_wrapper_factory(
            fn=fn,
            fn_type=fn_type,
            span_type=span_type,
            name=name,
            prune_empty=prune_empty,
            recursive=False,
            filter=filter,
            depth=depth,
            compiled_ast=None,
            skip_modules=skip_modules,
            skip_functions=skip_functions,
        )

    # Remove decorators
    # TODO should only remove traced decorator
    func_def.decorator_list = []

    collector = TracerCallCollector(func_def.name)
    collector.visit(func_def)

    transformer = TracerCallTransformer(
        collector.get_local_function_names(),
        collector.get_external_call_names(),
    )
    transformer.visit(parsed_ast)
    ast.fix_missing_locations(parsed_ast)
    _traced_logger.debug(f"Compiling AST for {fn.__name__}")

    if _traced_logger_enabled:
        _print_tree_source_with_lineno(fn.__name__, parsed_ast)

    compiled_ast = compile(parsed_ast, filename="<ast>", mode="exec")

    return _trace_wrapper_factory(
        fn=fn,
        fn_type=fn_type,
        span_type=span_type,
        name=name,
        prune_empty=prune_empty,
        recursive=True,
        filter=filter,
        depth=depth - 1,
        compiled_ast=compiled_ast,
        skip_modules=skip_modules,
        skip_functions=skip_functions,
    )


def traced(
    obj: Union[Callable, ModuleType, Type[Any], Any] = None,
    *,
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
    initialize_trace_logger()

    if obj is None:
        # Any changes to the arguments of traced should be reflected here.
        return lambda f: traced(
            f,
            prune_empty=prune_empty,
            span_type=span_type,
            name=name,
            filter=filter,
            fn_type=fn_type,
            recursive=recursive,
            depth=depth,
            skip_modules=skip_modules,
            skip_functions=skip_functions,
        )

    if ACTIVE_TRACE_PARAMETERS.get() is not None:
        args = ACTIVE_TRACE_PARAMETERS.get()
        prune_empty = args["prune_empty"]
        span_type = args["span_type"]
        name = args["name"]
        filter = args["filter"]
        fn_type = args["fn_type"]
        recursive = args["recursive"]
        depth = args["depth"]
        skip_modules = args["skip_modules"]
        skip_functions = args["skip_functions"]

    if hasattr(obj, "__unify_traced") or (
        skip_modules is not None and inspect.getmodule(obj) in skip_modules
    ):
        return obj

    ret = None
    if inspect.isclass(obj):
        ret = _trace_class(
            obj,
            prune_empty,
            span_type,
            name,
            filter if filter else _default_trace_filter,
        )
    elif inspect.ismodule(obj):
        ret = _trace_module(
            obj,
            prune_empty,
            span_type,
            name,
            filter if filter else _default_trace_filter,
        )
    elif inspect.isfunction(obj) or inspect.ismethod(obj):
        if skip_functions is not None and obj in skip_functions:
            return obj

        if depth is None:
            depth = float("inf")
        ret = _trace_function(
            obj,
            prune_empty,
            span_type,
            name,
            filter,
            fn_type,
            recursive,
            depth,
            skip_modules,
            skip_functions,
        )
    else:
        ret = _trace_instance(
            obj,
            prune_empty,
            span_type,
            name,
            filter if filter else _default_trace_filter,
        )

    if ret is not None:
        try:
            setattr(ret, "__unify_traced", True)
        except (AttributeError, TypeError):
            pass

    return ret


class LogTransformer(ast.NodeTransformer):
    def __init__(self):
        super().__init__()
        self.param_names = []
        self.assigned_names = set()
        self._in_function = False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._in_function = True
        # Collect non-underscore params
        self.param_names = [
            arg.arg for arg in node.args.args if not arg.arg.startswith("_")
        ]
        # Collect non-underscore kwonlyargs
        self.param_names += [
            arg.arg for arg in node.args.kwonlyargs if not arg.arg.startswith("_")
        ]

        # Add **kwargs parameter if not already present
        if not node.args.kwarg:
            node.args.kwarg = ast.arg(arg="kwargs")

        # TODO: this is a hack to ensure that the function always returns something
        if not isinstance(node.body[-1], ast.Return):
            node.body.append(ast.Return(value=ast.Constant(value=None)))

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
                    # Remove from param_names if it's a reassigned parameter
                    if target.id in self.param_names:
                        self.param_names.remove(target.id)
                    self.assigned_names.add(target.id)
        return node

    def visit_Return(self, node: ast.Return):
        if not self._in_function:
            return node

        log_keywords = []
        # Add regular parameters (that weren't reassigned)
        for p in self.param_names:
            log_keywords.append(
                ast.keyword(arg=p, value=ast.Name(id=p, ctx=ast.Load())),
            )

        # Add assigned variables (including reassigned parameters)
        for var_name in sorted(self.assigned_names):
            log_keywords.append(
                ast.keyword(arg=var_name, value=ast.Name(id=var_name, ctx=ast.Load())),
            )

        # Add filtered kwargs (non-underscore keys)
        kwargs_dict = ast.DictComp(
            key=ast.Name(id="k", ctx=ast.Load()),
            value=ast.Name(id="v", ctx=ast.Load()),
            generators=[
                ast.comprehension(
                    target=ast.Tuple(
                        elts=[
                            ast.Name(id="k", ctx=ast.Store()),
                            ast.Name(id="v", ctx=ast.Store()),
                        ],
                        ctx=ast.Store(),
                    ),
                    iter=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id="kwargs", ctx=ast.Load()),
                            attr="items",
                            ctx=ast.Load(),
                        ),
                        args=[],
                        keywords=[],
                    ),
                    ifs=[
                        ast.UnaryOp(
                            op=ast.Not(),
                            operand=ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(id="k", ctx=ast.Load()),
                                    attr="startswith",
                                    ctx=ast.Load(),
                                ),
                                args=[ast.Constant(value="_")],
                                keywords=[],
                            ),
                        ),
                    ],
                    is_async=0,
                ),
            ],
        )
        log_keywords.append(ast.keyword(arg=None, value=kwargs_dict))

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

    # 4) Get the current module's globals
    module = inspect.getmodule(func)
    func_globals = module.__dict__.copy() if module else globals().copy()
    func_globals["unify_log"] = unify_log

    # 5) Execute the compiled module code in that namespace
    exec(code, func_globals)
    trans = func_globals[func.__name__]

    # 6 ) Add logging context
    def transformed_func(*args, **kwargs):
        with unify.Log():
            return trans(*args, **kwargs)

    # Copy necessary attributes
    transformed_func.__name__ = func.__name__
    transformed_func.__doc__ = func.__doc__
    transformed_func.__module__ = func.__module__
    transformed_func.__annotations__ = func.__annotations__

    # Copy closure and cell variables if they exist
    if func.__closure__:
        transformed_func.__closure__ = func.__closure__

    return transformed_func
