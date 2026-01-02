from __future__ import annotations

import ast
import inspect
import textwrap
from typing import Any, Dict, List, Optional, Union

from ..utils.helpers import _validate_api_key
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
        **entries,
    ):
        self._id = id
        self._future = _future
        self._ts = ts
        self._project = project
        self._context = context
        self._entries = entries
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

    # Dunders

    def __eq__(self, other: Union[dict, Log]) -> bool:
        if isinstance(other, dict):
            other = Log(id=other["id"], **other["entries"])
        if self._id is not None and other._id is not None:
            return self._id == other._id
        return self.to_json() == other.to_json()

    def __len__(self):
        return len(self._entries)

    def __repr__(self) -> str:
        return f"Log(id={self._id})"

    # Public

    def download(self):
        # If id is not yet resolved, wait for the future
        if self._id is None and self._future is not None:
            self._id = self._future.result(timeout=5)
        log = get_log_by_id(id=self._id, api_key=self._api_key)
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
            "project": self._project,
            "context": self._context,
            "entries": self._entries,
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


def set_context(
    context: str,
    mode: str = "both",
    overwrite: bool = False,
    relative: bool = True,
    skip_create: bool = False,
):
    if mode == "both":
        if relative:
            assert CONTEXT_WRITE.get() == CONTEXT_READ.get()
            context = _join_path(CONTEXT_WRITE.get(), context)
            CONTEXT_WRITE.set(context)
            CONTEXT_READ.set(context)
        else:
            CONTEXT_WRITE.set(context)
            CONTEXT_READ.set(context)
    elif mode == "write":
        if relative:
            context = _join_path(CONTEXT_WRITE.get(), context)
            CONTEXT_WRITE.set(context)
        else:
            CONTEXT_WRITE.set(context)
    elif mode == "read":
        if relative:
            context = _join_path(CONTEXT_READ.get(), context)
            CONTEXT_READ.set(context)
        else:
            CONTEXT_READ.set(context)

    if skip_create:
        assert (
            skip_create and not overwrite
        ), "Cannot skip create and overwrite at the same time"
        return

    context_exists_remote = context in unify.get_contexts()
    if overwrite and context_exists_remote:
        if mode == "read":
            raise Exception(f"Cannot overwrite logs in read mode.")
        unify.delete_context(context)
    if not context_exists_remote:
        unify.create_context(context)


def unset_context():
    CONTEXT_WRITE.set("")
    CONTEXT_READ.set("")


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

        if self._mode == "both":
            assert CONTEXT_WRITE.get() == CONTEXT_READ.get()
            self._context = _join_path(CONTEXT_WRITE.get(), self._context)
            self._context_write_token = CONTEXT_WRITE.set(self._context)
            self._context_read_token = CONTEXT_READ.set(self._context)
        elif self._mode == "write":
            self._context = _join_path(CONTEXT_WRITE.get(), self._context)
            self._context_write_token = CONTEXT_WRITE.set(self._context)
        elif self._mode == "read":
            self._context = _join_path(CONTEXT_READ.get(), self._context)
            self._context_read_token = CONTEXT_READ.set(self._context)

        context_exists_remote = self._context in unify.get_contexts()

        if not context_exists_remote:
            unify.create_context(self._context, is_versioned=self._is_versioned)
        elif self._overwrite and context_exists_remote:
            if self._mode == "read":
                raise Exception(f"Cannot overwrite logs in read mode.")

            unify.delete_context(self._context)
            unify.create_context(self._context, is_versioned=self._is_versioned)

    def __exit__(self, *args, **kwargs):
        if self._mode == "both":
            assert CONTEXT_WRITE.get() == CONTEXT_READ.get()
            CONTEXT_WRITE.reset(self._context_write_token)
            CONTEXT_READ.reset(self._context_read_token)
        elif self._mode == "write":
            CONTEXT_WRITE.reset(self._context_write_token)
        elif self._mode == "read":
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
        _validate_mode_nesting(ACTIVE_ENTRIES_MODE.get(), self._mode)
        self._mode_token = ACTIVE_ENTRIES_MODE.set(self._mode)

        if self._mode in ("both", "write"):
            self._entries_token_write = ACTIVE_ENTRIES_WRITE.set(
                {**ACTIVE_ENTRIES_WRITE.get(), **{"experiment": self._name}},
            )
            self._nest_token = ENTRIES_NEST_LEVEL.set(
                ENTRIES_NEST_LEVEL.get() + 1,
            )
        if self._mode in ("both", "read"):
            self._entries_read_token = ACTIVE_ENTRIES_READ.set(
                {**ACTIVE_ENTRIES_READ.get(), **{"experiment": self._name}},
            )

        if self._overwrite:
            if self._mode == "read":
                raise Exception(f"Cannot overwrite logs in read mode.")

            logs = unify.get_logs(return_ids_only=True)
            if len(logs) > 0:
                unify.delete_logs(logs=logs)

    def __exit__(self, *args, **kwargs):
        ACTIVE_ENTRIES_MODE.reset(self._mode_token)
        if self._mode in ("both", "write"):
            ACTIVE_ENTRIES_WRITE.reset(self._entries_token_write)
            ENTRIES_NEST_LEVEL.reset(self._nest_token)
            if ENTRIES_NEST_LEVEL.get() == 0:
                LOGGED.set({})
        if self._mode in ("both", "read"):
            ACTIVE_ENTRIES_READ.reset(self._entries_read_token)


class LogTransformer(ast.NodeTransformer):
    def __init__(self):
        super().__init__()
        self.param_names = []
        self.assigned_names = set()
        self._in_function = False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._in_function = True
        # Collect non-underscore function arguments
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
        # Add regular function arguments (that weren't reassigned)
        for p in self.param_names:
            log_keywords.append(
                ast.keyword(arg=p, value=ast.Name(id=p, ctx=ast.Load())),
            )

        # Add assigned variables (including reassigned function arguments)
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
    function arguments, and assigned variables.
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
