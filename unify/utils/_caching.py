import json
import os
import threading
from pydantic import BaseModel
from typing import Dict, Optional, Union, Any
from openai.types.chat import ChatCompletion

_cache: Optional[Dict] = None
_cache_dir = (
    os.environ["UNIFY_CACHE_DIR"] if "UNIFY_CACHE_DIR" in os.environ else os.getcwd()
)
_cache_fpath: str = os.path.join(_cache_dir, ".cache.json")

CACHE_LOCK = threading.Lock()


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
    kw_str = json.dumps(kw)
    if kw_str in _cache:
        ret = ChatCompletion(**json.loads(_cache[kw_str]))
        CACHE_LOCK.release()
        return ret
    CACHE_LOCK.release()


def _dumps(obj: Any) -> Any:
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    elif hasattr(obj, "to_json"):
        return obj.to_json()
    elif isinstance(obj, dict):
        return json.dumps({k: _dumps(v) for k, v in obj.items()})
    elif isinstance(obj, list):
        return json.dumps([_dumps(v) for v in obj])
    elif isinstance(obj, tuple):
        return json.dumps(tuple(_dumps(v) for v in obj))
    else:
        return obj


# noinspection PyTypeChecker,PyUnresolvedReferences
def _write_to_cache(kw, response):
    global CACHE_LOCK
    CACHE_LOCK.acquire()
    _create_cache_if_none()
    kw = {k: v for k, v in kw.items() if v is not None}
    kw_str = _dumps(kw)
    response_str = _dumps(response)
    _cache[kw_str] = response_str
    with open(_cache_fpath, "w") as outfile:
        json.dump(_cache, outfile)
    CACHE_LOCK.release()
