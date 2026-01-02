"""
Main caching module providing high-level caching functionality.

This module provides decorators and utilities for caching function results
with multiple backend options and flexible caching modes.
"""

import difflib
import json
import threading
from typing import Any, Dict, Optional, Type

from litellm.types.utils import ModelResponse
from openai.types.chat import ChatCompletion, ParsedChatCompletion
from pydantic import BaseModel
from unify.utils.caching import BaseCache, LocalCache, LocalSeparateCache, RemoteCache
from unify.utils.caching.cache_benchmark import record_get_cache, record_write_to_cache

# Global state
CACHE_LOCK = threading.Lock()
CACHING_ENABLED = False
CURRENT_CACHE_BACKEND = "local"

# Available cache backends
CACHE_BACKENDS = {
    "local": LocalCache,
    "remote": RemoteCache,
    "local_separate": LocalSeparateCache,
}


def set_cache_backend(backend: str) -> None:
    """Set the current cache backend."""
    global CURRENT_CACHE_BACKEND
    if backend not in CACHE_BACKENDS:
        raise ValueError(
            f"Invalid backend: {backend}. Available: {list(CACHE_BACKENDS.keys())}",
        )
    CURRENT_CACHE_BACKEND = backend


def get_cache_backend(backend: Optional[str] = None) -> Type[BaseCache]:
    """Get the cache backend class."""
    if backend is None:
        backend = CURRENT_CACHE_BACKEND
    if backend not in CACHE_BACKENDS:
        raise ValueError(
            f"Invalid backend: {backend}. Available: {list(CACHE_BACKENDS.keys())}",
        )
    return CACHE_BACKENDS[backend]


def is_caching_enabled() -> bool:
    """Check if caching is globally enabled."""
    return CACHING_ENABLED


def _minimal_char_diff(a: str, b: str, context: int = 5) -> str:
    matcher = difflib.SequenceMatcher(None, a, b)
    diff_parts = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            segment = a[i1:i2]
            # If the segment is too long, show only a context at the beginning and end.
            if len(segment) > 2 * context:
                diff_parts.append(segment[:context] + "..." + segment[-context:])
            else:
                diff_parts.append(segment)
        elif tag == "replace":
            diff_parts.append(f"[{a[i1:i2]}|{b[j1:j2]}]")
        elif tag == "delete":
            diff_parts.append(f"[-{a[i1:i2]}-]")
        elif tag == "insert":
            diff_parts.append(f"[+{b[j1:j2]}+]")

    return "".join(diff_parts)


@record_get_cache
def _get_cache(
    fn_name: str,
    kw: Dict[str, Any],
    filename: str = None,
    raise_on_empty: bool = False,
    read_closest: bool = False,
    delete_closest: bool = False,
    backend: Optional[str] = None,
) -> Optional[Any]:
    global CACHE_LOCK
    # Prevents circular import
    from unify.logging.logs import Log

    type_mapping = {
        "ChatCompletion": ChatCompletion,
        "ModelResponse": ModelResponse,
        "Log": Log,
        "ParsedChatCompletion": ParsedChatCompletion,
    }
    CACHE_LOCK.acquire()
    try:
        current_backend = get_cache_backend(backend)
        current_backend.initialize_cache(filename)
        kw = {k: v for k, v in kw.items() if v is not None}
        kw_str = BaseCache.serialize_object(kw)
        cache_str = f"{fn_name}_{kw_str}"
        if not current_backend.has_key(cache_str):
            if raise_on_empty or read_closest:
                keys_to_search = current_backend.list_keys()
                if len(keys_to_search) == 0:
                    CACHE_LOCK.release()
                    raise Exception(
                        f"Failed to get cache for function {fn_name} with kwargs {BaseCache.serialize_object(kw, indent=4)} "
                        f"Cache is empty, mode is read-only ",
                    )
                closest_match = difflib.get_close_matches(
                    cache_str,
                    keys_to_search,
                    n=1,
                    cutoff=0,
                )[0]
                minimal_char_diff = _minimal_char_diff(cache_str, closest_match)
                if read_closest:
                    cache_str = closest_match
                else:
                    CACHE_LOCK.release()
                    raise Exception(
                        f"Failed to get cache for function {fn_name} with kwargs {BaseCache.serialize_object(kw, indent=4)} "
                        f"from cache at {filename}. \n\nCorresponding key\n{cache_str}\nwas not found in the cache.\n\n"
                        f"The closest match is:\n{closest_match}\n\n"
                        f"The contracted diff is:\n{minimal_char_diff}\n\n",
                    )
            else:
                CACHE_LOCK.release()
                return
        ret, res_types = current_backend.retrieve_entry(cache_str)
        if res_types is None:
            CACHE_LOCK.release()
            return ret
        for idx_str, type_str in res_types.items():
            type_str = type_str.split("[")[0]
            idx_list = json.loads(idx_str)
            if len(idx_list) == 0:
                if read_closest and delete_closest:
                    current_backend.remove_entry(cache_str)
                CACHE_LOCK.release()
                typ = type_mapping[type_str]
                if issubclass(typ, BaseModel):
                    return typ(**ret)
                elif issubclass(typ, Log):
                    return typ.from_json(ret)
                raise Exception(f"Cache indexing found for unsupported type: {typ}")
            item = ret
            for i, idx in enumerate(idx_list):
                if i == len(idx_list) - 1:
                    typ = type_mapping[type_str]
                    if issubclass(typ, BaseModel) or issubclass(typ, Log):
                        item[idx] = typ.from_json(item[idx])
                    else:
                        raise Exception(
                            f"Cache indexing found for unsupported type: {typ}",
                        )
                    break
                item = item[idx]
        if read_closest and delete_closest:
            current_backend.remove_entry(cache_str)
        CACHE_LOCK.release()
        return ret
    except Exception as e:
        if CACHE_LOCK.locked():
            CACHE_LOCK.release()
        raise Exception(
            f"Failed to get cache for function {fn_name} with kwargs {kw} "
            f"from cache at {filename}",
        ) from e


@record_write_to_cache
def _write_to_cache(
    fn_name: str,
    kw: Dict[str, Any],
    response: Any,
    backend: Optional[str] = None,
    filename: str = None,
):

    global CACHE_LOCK
    CACHE_LOCK.acquire()
    try:
        current_backend = get_cache_backend(backend)
        current_backend.initialize_cache(filename)
        kw = {k: v for k, v in kw.items() if v is not None}
        kw_str = BaseCache.serialize_object(kw)
        cache_str = f"{fn_name}_{kw_str}"
        res_types = {}
        response_str = BaseCache.serialize_object(response, res_types)
        current_backend.store_entry(
            key=cache_str,
            value=response_str,
            res_types=res_types if len(res_types) > 0 else None,
        )
        CACHE_LOCK.release()
    except Exception as e:
        CACHE_LOCK.release()
        raise Exception(
            f"Failed to write function {fn_name} with kwargs {kw} and "
            f"response {response} to cache at {filename}",
        ) from e
