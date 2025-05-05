import inspect
import json
import os
import threading
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
import unify
from pydantic import BaseModel, ValidationError

PROJECT_LOCK = threading.Lock()


class RequestError(Exception):
    def __init__(self, response: requests.Response):
        req = response.request
        message = (
            f"{req.method} {req.url} failed with status code {response.status_code}. "
            f"Request body: {req.body}, Response: {response.text}"
        )
        super().__init__(message)
        self.response = response


def _check_response(response: requests.Response):
    if not response.ok:
        raise RequestError(response)


def _res_to_list(response: requests.Response) -> Union[List, Dict]:
    return json.loads(response.text)


def _validate_api_key(api_key: Optional[str]) -> str:
    if api_key is None:
        api_key = os.environ.get("UNIFY_KEY")
    if api_key is None:
        raise KeyError(
            "UNIFY_KEY is missing. Please make sure it is set correctly!",
        )
    return api_key


def _default(value: Any, default_value: Any) -> Any:
    return value if value is not None else default_value


def _dict_aligns_with_pydantic(dict_in: Dict, pydantic_cls: type(BaseModel)) -> bool:
    try:
        pydantic_cls.model_validate(dict_in)
        return True
    except ValidationError:
        return False


def _make_json_serializable(
    item: Union[Dict, List, Tuple],
) -> Union[Dict, List, Tuple]:
    if isinstance(item, list):
        return [_make_json_serializable(i) for i in item]
    elif isinstance(item, dict):
        return {k: _make_json_serializable(v) for k, v in item.items()}
    elif isinstance(item, tuple):
        return tuple(_make_json_serializable(i) for i in item)
    elif inspect.isclass(item) and issubclass(item, BaseModel):
        return item.schema()
    elif isinstance(item, BaseModel):
        return item.dict()
    elif hasattr(item, "json") and callable(item.json):
        return _make_json_serializable(item.json())
    else:
        try:
            json.dumps(item)
            return item
        except:
            return str(item)


def _get_and_maybe_create_project(
    project: Optional[str] = None,
    required: bool = True,
    api_key: Optional[str] = None,
    create_if_missing: bool = True,
) -> Optional[str]:
    # noinspection PyUnresolvedReferences
    from unify.logging.utils.logs import ASYNC_LOGGING

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
    if ASYNC_LOGGING:
        # acquiring the project lock here will block the async logger
        # so we skip the lock if we are in async mode
        return project
    with PROJECT_LOCK:
        if project not in unify.list_projects(api_key=api_key):
            unify.create_project(project, api_key=api_key)
    return project


def _prune_dict(val):
    def keep(v):
        if v in (None, "NOT_GIVEN"):
            return False
        else:
            ret = _prune_dict(v)
            if isinstance(ret, dict) or isinstance(ret, list) or isinstance(ret, tuple):
                return bool(ret)
            return True

    if (
        not isinstance(val, dict)
        and not isinstance(val, list)
        and not isinstance(val, tuple)
    ):
        return val
    elif isinstance(val, dict):
        return {k: _prune_dict(v) for k, v in val.items() if keep(v)}
    elif isinstance(val, list):
        return [_prune_dict(v) for i, v in enumerate(val) if keep(v)]
    else:
        return tuple(_prune_dict(v) for i, v in enumerate(val) if keep(v))


import copy
from typing import Any, Dict, List, Set, Tuple, Union

__all__ = ["flexible_deepcopy"]


# Internal sentinel: return this to signal “skip me”.
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
