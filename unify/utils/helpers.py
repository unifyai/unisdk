import os
import threading
from typing import Optional

import unify

PROJECT_LOCK = threading.Lock()


def _validate_api_key(api_key: Optional[str]) -> str:
    if api_key is None:
        api_key = os.environ.get("UNIFY_KEY")
    if api_key is None:
        raise KeyError(
            "UNIFY_KEY is missing. Please make sure it is set correctly!",
        )
    return api_key


def _create_request_header(api_key: Optional[str]) -> dict:
    return {
        "Authorization": f"Bearer {_validate_api_key(api_key)}",
        "accept": "application/json",
        "Content-Type": "application/json",
    }


def _get_and_maybe_create_project(
    project: Optional[str] = None,
    required: bool = True,
    api_key: Optional[str] = None,
    create_if_missing: bool = False,
) -> Optional[str]:
    api_key = _validate_api_key(api_key)
    if project is None:
        project = unify.active_project()
        if project is None:
            if required:
                project = "_"
            else:
                return None
    if not create_if_missing:
        return project
    with PROJECT_LOCK:
        if project not in unify.list_projects(api_key=api_key):
            unify.create_project(project, api_key=api_key)
    return project


import copy
from typing import Any, Dict, List, Set, Tuple, Union

__all__ = ["flexible_deepcopy"]


# Internal sentinel: return this to signal "skip me".
class _SkipType:
    pass


_SKIP = _SkipType()

Container = Union[Dict[Any, Any], List[Any], Tuple[Any, ...], Set[Any]]


def flexible_deepcopy(
    obj: Any,
    on_fail: str = "raise",
    _memo: Optional[Dict[int, Any]] = None,
) -> Any:
    """
    Perform a deepcopy that tolerates un‑copyable elements.

    Parameters
    ----------
    obj : Any
        The object you wish to copy.
    on_fail : {'raise', 'skip', 'shallow'}, default 'raise'
        • 'raise'   – re‑raise copy error (standard behaviour).
        • 'skip'    – drop the offending element from the result.
        • 'shallow' – insert the original element unchanged.
    _memo : dict or None (internal)
        Memoisation dict to preserve identity & avoid infinite recursion.

    Returns
    -------
    Any
        A deep‑copied version of *obj*, modified per *on_fail* strategy.

    Raises
    ------
    ValueError
        If *on_fail* is not one of the accepted values.
    Exception
        Re‑raises whatever copy error occurred when *on_fail* == 'raise'.
    """
    if _memo is None:
        _memo = {}

    obj_id = id(obj)
    if obj_id in _memo:  # Handle circular references.
        return _memo[obj_id]

    def _attempt(value: Any) -> Union[Any, _SkipType]:
        """Try to deepcopy *value*; fall back per on_fail."""
        try:
            return flexible_deepcopy(value, on_fail, _memo)
        except Exception:
            if on_fail == "raise":
                raise
            if on_fail == "shallow":
                return value
            if on_fail == "skip":
                return _SKIP
            raise ValueError(f"Invalid on_fail option: {on_fail!r}")

    # --- Handle built‑in containers explicitly ---------------------------
    if isinstance(obj, dict):
        result: Dict[Any, Any] = {}
        _memo[obj_id] = result  # Early memoisation for cycles
        for k, v in obj.items():
            nk = _attempt(k)
            nv = _attempt(v)
            if _SKIP in (nk, nv):  # Skip entry if key or value failed
                continue
            result[nk] = nv
        return result

    if isinstance(obj, list):
        result: List[Any] = []
        _memo[obj_id] = result
        for item in obj:
            nitem = _attempt(item)
            if nitem is not _SKIP:
                result.append(nitem)
        return result

    if isinstance(obj, tuple):
        items = []
        _memo[obj_id] = None  # Placeholder for circular refs
        for item in obj:
            nitem = _attempt(item)
            if nitem is not _SKIP:
                items.append(nitem)
        result = tuple(items)
        _memo[obj_id] = result
        return result

    if isinstance(obj, set):
        result: Set[Any] = set()
        _memo[obj_id] = result
        for item in obj:
            nitem = _attempt(item)
            if nitem is not _SKIP:
                result.add(nitem)
        return result

    # --- Non‑container: fall back to standard deepcopy -------------------
    try:
        result = copy.deepcopy(obj, _memo)
        _memo[obj_id] = result
        return result
    except Exception:
        if on_fail == "raise":
            raise
        if on_fail == "shallow":
            _memo[obj_id] = obj
            return obj
        if on_fail == "skip":
            return _SKIP
        raise ValueError(f"Invalid on_fail option: {on_fail!r}")
