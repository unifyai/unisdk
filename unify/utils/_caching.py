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

CACHING = False
CACHE_FNAME = ".cache.json"


def set_caching(value: bool) -> None:
    global CACHING, CACHE_FNAME
    CACHING = value


def set_caching_fname(value: Optional[str] = None) -> None:
    global CACHE_FNAME
    if value is not None:
        CACHE_FNAME = value
    else:
        CACHE_FNAME = ".cache.json"


def _get_caching():
    return CACHING


def _get_caching_fname():
    return CACHE_FNAME


def _create_cache_if_none(filename: str = None):
    global _cache, _cache_fpath, _cache_dir
    if filename is None:
        cache_fpath = _cache_fpath
    else:
        cache_fpath = os.path.join(_cache_dir, filename)
    if _cache is None:
        if not os.path.exists(cache_fpath):
            with open(cache_fpath, "w") as outfile:
                json.dump({}, outfile)
        with open(cache_fpath) as outfile:
            _cache = json.load(outfile)


# noinspection PyTypeChecker,PyUnboundLocalVariable
def _get_cache(fn_name: str, kw: Dict[str, Any], filename: str = None) -> Optional[Any]:
    global CACHE_LOCK
    # prevents circular import
    from unify.evals.logging import Log

    type_str_to_type = {
        "ChatCompletion": ChatCompletion,
        "Log": Log,
    }
    CACHE_LOCK.acquire()
    _create_cache_if_none(filename)
    kw = {k: v for k, v in kw.items() if v is not None}
    kw_str = _dumps(kw)
    cache_str = fn_name + "_" + kw_str
    if cache_str not in _cache:
        CACHE_LOCK.release()
        return
    ret = json.loads(_cache[cache_str])
    if cache_str + "_res_types" not in _cache:
        CACHE_LOCK.release()
        return ret
    for idx_str, type_str in _cache[cache_str + "_res_types"].items():
        idx_list = json.loads(idx_str)
        if len(idx_list) == 0:
            CACHE_LOCK.release()
            typ = type_str_to_type[type_str]
            if issubclass(typ, BaseModel):
                return type_str_to_type[type_str](**ret)
            elif issubclass(typ, Log):
                return type_str_to_type[type_str].from_json(ret)
            raise Exception(f"Cache indexing found for unsupported type: {typ}")
        item = ret
        for i, idx in enumerate(idx_list):
            if i == len(idx_list) - 1:
                typ = type_str_to_type[type_str]
                if issubclass(typ, BaseModel) or issubclass(typ, Log):
                    item[idx] = type_str_to_type[type_str].from_json(item[idx])
                else:
                    raise Exception(f"Cache indexing found for unsupported type: {typ}")
                break
            item = item[idx]
    CACHE_LOCK.release()
    return ret


def _dumps(
    obj: Any,
    cached_types: Dict[str, str] = None,
    idx: List[Union[str, int]] = None,
) -> Any:
    # prevents circular import
    from unify.evals.logging import Log

    base = False
    if idx is None:
        base = True
        idx = list()
    if isinstance(obj, BaseModel):
        if cached_types is not None:
            cached_types[json.dumps(idx)] = obj.__class__.__name__
        ret = obj.model_dump()
    elif isinstance(obj, Log):
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
    return json.dumps(ret) if base else ret


# noinspection PyTypeChecker,PyUnresolvedReferences
def _write_to_cache(
    fn_name: str,
    kw: Dict[str, Any],
    response: Any,
    filename: str = None,
):
    global CACHE_LOCK
    CACHE_LOCK.acquire()
    _create_cache_if_none(filename)
    kw = {k: v for k, v in kw.items() if v is not None}
    kw_str = _dumps(kw)
    cache_str = fn_name + "_" + kw_str
    _res_types = {}
    response_str = _dumps(response, _res_types)
    if _res_types:
        _cache[cache_str + "_res_types"] = _res_types
    _cache[cache_str] = response_str
    if filename is None:
        cache_fpath = _cache_fpath
    else:
        cache_fpath = os.path.join(_cache_dir, filename)
    with open(cache_fpath, "w") as outfile:
        json.dump(_cache, outfile)
    CACHE_LOCK.release()
