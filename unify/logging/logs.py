from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import unify

from ..utils.helpers import _validate_api_key
from .utils.logs import (
    ACTIVE_LOG,
    CONTEXT_READ,
    CONTEXT_WRITE,
    delete_logs,
    update_logs,
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

    def update_entries(self, **entries) -> None:
        update_logs(
            logs=self._id,
            api_key=self._api_key,
            context=self._context,
            entries=entries,
            overwrite=True,
        )
        self._entries = {**self._entries, **entries}

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
            self._id = self._future.result(timeout=5)
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
