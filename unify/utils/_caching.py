import os
import json
import threading
from pydantic import BaseModel
from typing import Dict, Optional, Union, Any, List
from openai.types.chat import ChatCompletion

_cache: Optional[Dict] = None
_cache_dir = (
    os.environ["UNIFY_CACHE_DIR"] if "UNIFY_CACHE_DIR" in os.environ else os.getcwd()
)
_cache_fpath: str = os.path.join(_cache_dir, ".cache.json")

CACHE_LOCK = threading.Lock()
TYPE_STR_TO_TYPE = {
    "ChatCompletion": ChatCompletion,
}


def _create_cache_if_none():
    global _cache
    if _cache is None:
        if not os.path.exists(_cache_fpath):
            with open(_cache_fpath, "w") as outfile:
                json.dump({}, outfile)
        with open(_cache_fpath) as outfile:
            _cache = json.load(outfile)


# noinspection PyTypeChecker,PyUnboundLocalVariable
def _get_cache(kw: Dict[str, Any]) -> Union[None, Dict]:
    global CACHE_LOCK
    CACHE_LOCK.acquire()
    _create_cache_if_none()
    kw = {k: v for k, v in kw.items() if v is not None}
    kw_str = _dumps(kw)
    if kw_str not in _cache:
        CACHE_LOCK.release()
        return
    ret = json.loads(_cache[kw_str])
    if kw_str + "_res_types" not in _cache:
        CACHE_LOCK.release()
        return ret
    for idx_str, type_str in _cache[kw_str + "_res_types"].items():
        idx_list = json.loads(idx_str)
        if len(idx_list) == 0:
            CACHE_LOCK.release()
            if type_str == "ChatCompletion":
                return TYPE_STR_TO_TYPE[type_str](**ret)
            return TYPE_STR_TO_TYPE[type_str](ret)
        item = ret
        for i, idx in enumerate(idx_list):
            if i == len(idx_list) - 1:
                item[idx] = TYPE_STR_TO_TYPE[type_str](item[idx][-1])
                break
            item = item[idx]
    CACHE_LOCK.release()
    return ret


def _dumps(
    obj: Any,
    cached_types: Dict[str, str] = None,
    idx: List[Union[str, int]] = None,
) -> Any:
    base = False
    if idx is None:
        base = True
        idx = list()
    if isinstance(obj, BaseModel):
        if cached_types is not None:
            cached_types[json.dumps(idx)] = obj.__class__.__name__
        ret = obj.model_dump()
    elif hasattr(obj, "to_json"):
        if cached_types is not None:
            cached_types[json.dumps(idx)] = obj.__class__.__name__
        ret = obj.to_json()
    elif isinstance(obj, dict):
        ret = {k: _dumps(v, cached_types, idx + ["k"]) for k, v in obj.items()}
    elif isinstance(obj, list):
        ret = [_dumps(v, cached_types, idx + [i]) for i, v in enumerate(obj)]
    elif isinstance(obj, tuple):
        ret = tuple(_dumps(v, cached_types, idx + [i]) for i, v in enumerate(obj))
    else:
        ret = obj
    return json.dumps(ret) if base else base


# noinspection PyTypeChecker,PyUnresolvedReferences
def _write_to_cache(kw, response):
    global CACHE_LOCK
    CACHE_LOCK.acquire()
    _create_cache_if_none()
    kw = {k: v for k, v in kw.items() if v is not None}
    kw_str = _dumps(kw)
    _res_types = {}
    response_str = _dumps(response, _res_types)
    if _res_types:
        _cache[kw_str + "_res_types"] = _res_types
    _cache[kw_str] = response_str
    with open(_cache_fpath, "w") as outfile:
        json.dump(_cache, outfile)
    CACHE_LOCK.release()
