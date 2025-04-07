from __future__ import annotations

import ast
import textwrap
import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from ..utils.helpers import _make_json_serializable, _prune_dict, _validate_api_key
from .utils.compositions import *
from .utils.logs import _handle_special_types
from .utils.logs import log as unify_log

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
        add_log_entries(logs=self._id, api_key=self._api_key, **entries)
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


class Context:
    def __init__(self, context: str, mode: str = "both", overwrite: bool = False):
        self._context = context
        _validate_mode(mode)
        self._mode = mode
        self._overwrite = overwrite

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
            unify.create_context(self._context)

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


def _nested_add(a, b):
    if a is None and isinstance(b, dict):
        a = {k: None if isinstance(v, dict) else 0 for k, v in b.items()}
    elif b is None and isinstance(a, dict):
        b = {k: None if isinstance(v, dict) else 0 for k, v in a.items()}
    if isinstance(a, dict) and isinstance(b, dict):
        return {k: _nested_add(a[k], b[k]) for k in a if k in b}
    elif a is None and b is None:
        return None
    return a + b


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
            name=name,
            trace_contexts=trace_contexts,
        )

    def wrapped(*args, **kwargs):
        log_token = None if ACTIVE_LOG.get() else ACTIVE_LOG.set([unify.log()])
        t1 = time.perf_counter()
        ts = datetime.now(timezone.utc).isoformat()
        if not SPAN.get():
            RUNNING_TIME.set(t1)
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
        new_span = {
            "id": str(uuid.uuid4()),
            "type": span_type,
            "parent_span_id": (None if not SPAN.get() else SPAN.get()["id"]),
            "span_name": fn.__name__ if name_w_sub is None else name_w_sub,
            "exec_time": None,
            "timestamp": ts,
            "offset": round(
                0.0 if not SPAN.get() else t1 - RUNNING_TIME.get(),
                2,
            ),
            "llm_usage": None,
            "llm_usage_inc_cache": None,
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
            new_span["errors"] = traceback.format_exc()
            raise e
        finally:
            outputs = _make_json_serializable(result) if result is not None else None
            t2 = time.perf_counter()
            exec_time = t2 - t1
            SPAN.get()["exec_time"] = exec_time
            SPAN.get()["outputs"] = outputs
            if SPAN.get()["type"] == "llm" and outputs is not None:
                SPAN.get()["llm_usage"] = outputs["usage"]
            if SPAN.get()["type"] in ("llm", "llm-cached") and outputs is not None:
                SPAN.get()["llm_usage_inc_cache"] = outputs["usage"]
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
                SPAN.get()["llm_usage"] = _nested_add(
                    SPAN.get()["llm_usage"],
                    new_span["llm_usage"],
                )
                SPAN.get()["llm_usage_inc_cache"] = _nested_add(
                    SPAN.get()["llm_usage_inc_cache"],
                    new_span["llm_usage_inc_cache"],
                )
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
