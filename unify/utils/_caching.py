import difflib
import inspect
import json
import os
import threading
from typing import Any, Dict, List, Optional, Union

from openai.types.chat import ChatCompletion, ParsedChatCompletion
from pydantic import BaseModel

_cache: Optional[Dict] = None
_cache_dir = (
    os.environ["UNIFY_CACHE_DIR"] if "UNIFY_CACHE_DIR" in os.environ else os.getcwd()
)
_cache_fpath: str = os.path.join(_cache_dir, ".cache.json")

CACHE_LOCK = threading.Lock()

CACHING = False
CACHE_FNAME = ".cache.json"
UPSTREAM_CACHE_CONTEXT_NAME = "UNIFY_CACHE"


def set_caching(value: bool) -> None:
    global CACHING, CACHE_FNAME
    CACHING = value


def set_caching_fname(value: Optional[str] = None) -> None:
    global CACHE_FNAME, _cache
    if value is not None:
        CACHE_FNAME = value
    else:
        CACHE_FNAME = ".cache.json"
    _cache = None  # Force a reload of the cache


def _get_caching():
    return CACHING


def _get_caching_fname():
    return CACHE_FNAME


def _get_caching_fpath():
    global _cache_dir, CACHE_FNAME
    return os.path.join(_cache_dir, CACHE_FNAME)


def _create_cache_if_none(filename: str = None, local: bool = True):
    from unify import create_context, get_contexts

    if not local:
        if UPSTREAM_CACHE_CONTEXT_NAME not in get_contexts():
            create_context(UPSTREAM_CACHE_CONTEXT_NAME)
        return

    global _cache, _cache_fpath, _cache_dir
    if filename is None:
        cache_fpath = _get_caching_fpath()
    else:
        cache_fpath = os.path.join(_cache_dir, filename)
    if _cache is None:
        if not os.path.exists(cache_fpath):
            with open(cache_fpath, "w") as outfile:
                json.dump({}, outfile)
        with open(cache_fpath) as outfile:
            _cache = json.load(outfile)


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


def _get_filter_expr(cache_key: str):
    return f"key == {json.dumps(cache_key)}"


def _get_entry_from_cache(cache_key: str, local: bool = True):
    from unify import get_logs

    value = res_types = None

    if local:
        if cache_key in _cache:
            value = json.loads(_cache[cache_key])
        if cache_key + "_res_types" in _cache:
            res_types = _cache[cache_key + "_res_types"]
    else:
        logs = get_logs(
            context=UPSTREAM_CACHE_CONTEXT_NAME,
            filter=_get_filter_expr(cache_key),
        )
        if len(logs) > 0:
            entry = logs[0].entries
            value = json.loads(entry["value"])
            if "res_types" in entry:
                res_types = json.loads(entry["res_types"])

    return value, res_types


def _is_key_in_cache(cache_key: str, local: bool = True):
    from unify import get_logs

    if local:
        return cache_key in _cache
    else:
        logs = get_logs(
            context=UPSTREAM_CACHE_CONTEXT_NAME,
            filter=_get_filter_expr(cache_key),
        )
        return len(logs) > 0


def _delete_from_cache(cache_str: str, local: bool = True):
    from unify.logging.logs import delete_logs, get_logs

    if local:
        del _cache[cache_str]
        del _cache[cache_str + "_res_types"]
    else:
        logs = get_logs(
            context=UPSTREAM_CACHE_CONTEXT_NAME,
            filter=_get_filter_expr(cache_str),
        )
        delete_logs(context=UPSTREAM_CACHE_CONTEXT_NAME, logs=logs)


def _get_cache_keys(local: bool = True):
    from unify import get_logs

    if local:
        return list(_cache.keys())
    else:
        logs = get_logs(context=UPSTREAM_CACHE_CONTEXT_NAME)
        return [log.entries["key"] for log in logs]


# noinspection PyTypeChecker,PyUnboundLocalVariable
def _get_cache(
    fn_name: str,
    kw: Dict[str, Any],
    filename: str = None,
    raise_on_empty: bool = False,
    read_closest: bool = False,
    delete_closest: bool = False,
    local: bool = True,
) -> Optional[Any]:
    global CACHE_LOCK
    # prevents circular import
    from unify.logging.logs import Log

    type_str_to_type = {
        "ChatCompletion": ChatCompletion,
        "Log": Log,
        "ParsedChatCompletion": ParsedChatCompletion,
    }
    CACHE_LOCK.acquire()
    # noinspection PyBroadException
    try:
        _create_cache_if_none(filename, local)
        kw = {k: v for k, v in kw.items() if v is not None}
        kw_str = _dumps(kw)
        cache_str = fn_name + "_" + kw_str
        if not _is_key_in_cache(cache_str, local):
            if raise_on_empty or read_closest:
                keys_to_search = _get_cache_keys(local)
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
                        f"Failed to get cache for function {fn_name} with kwargs {_dumps(kw, indent=4)} "
                        f"from cache at {filename}. \n\nCorresponding key\n{cache_str}\nwas not found in the cache.\n\n"
                        f"The closest match is:\n{closest_match}\n\n"
                        f"The contracted diff is:\n{minimal_char_diff}\n\n",
                    )
            else:
                CACHE_LOCK.release()
                return
        ret, res_types = _get_entry_from_cache(cache_str, local)
        if res_types is None:
            CACHE_LOCK.release()
            return ret
        for idx_str, type_str in res_types.items():
            type_str = type_str.split("[")[0]
            idx_list = json.loads(idx_str)
            if len(idx_list) == 0:
                if read_closest and delete_closest:
                    _delete_from_cache(cache_str, local)
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
                        raise Exception(
                            f"Cache indexing found for unsupported type: {typ}",
                        )
                    break
                item = item[idx]
        if read_closest and delete_closest:
            _delete_from_cache(cache_str, local)
        CACHE_LOCK.release()
        return ret
    except:
        if CACHE_LOCK.locked():
            CACHE_LOCK.release()
        raise Exception(
            f"Failed to get cache for function {fn_name} with kwargs {kw} "
            f"from cache at {filename}",
        )


def _dumps(
    obj: Any,
    cached_types: Dict[str, str] = None,
    idx: List[Union[str, int]] = None,
    indent: int = None,
) -> Any:
    # prevents circular import
    from unify.logging.logs import Log

    base = False
    if idx is None:
        base = True
        idx = list()
    if isinstance(obj, BaseModel):
        if cached_types is not None:
            cached_types[json.dumps(idx, indent=indent)] = obj.__class__.__name__
        ret = obj.model_dump()
    elif inspect.isclass(obj) and issubclass(obj, BaseModel):
        ret = obj.schema_json()
    elif isinstance(obj, Log):
        if cached_types is not None:
            cached_types[json.dumps(idx, indent=indent)] = obj.__class__.__name__
        ret = obj.to_json()
    elif isinstance(obj, dict):
        ret = {k: _dumps(v, cached_types, idx + ["k"]) for k, v in obj.items()}
    elif isinstance(obj, list):
        ret = [_dumps(v, cached_types, idx + [i]) for i, v in enumerate(obj)]
    elif isinstance(obj, tuple):
        ret = tuple(_dumps(v, cached_types, idx + [i]) for i, v in enumerate(obj))
    else:
        ret = obj
    return json.dumps(ret, indent=indent) if base else ret


# noinspection PyTypeChecker,PyUnresolvedReferences
def _write_to_cache(
    fn_name: str,
    kw: Dict[str, Any],
    response: Any,
    local: bool = True,
    filename: str = None,
):

    global CACHE_LOCK
    CACHE_LOCK.acquire()
    # noinspection PyBroadException
    try:
        _create_cache_if_none(filename, local)
        kw = {k: v for k, v in kw.items() if v is not None}
        kw_str = _dumps(kw)
        cache_str = fn_name + "_" + kw_str
        _res_types = {}
        response_str = _dumps(response, _res_types)
        if local:
            if _res_types:
                _cache[cache_str + "_res_types"] = _res_types
            _cache[cache_str] = response_str
            if filename is None:
                cache_fpath = _get_caching_fpath()
            else:
                cache_fpath = os.path.join(_cache_dir, filename)
            with open(cache_fpath, "w") as outfile:
                json.dump(_cache, outfile)
        else:
            # prevents circular import
            from unify.logging.logs import delete_logs, get_logs, log

            logs = get_logs(
                context=UPSTREAM_CACHE_CONTEXT_NAME,
                filter=_get_filter_expr(cache_str),
            )
            if len(logs) > 0:
                delete_logs(logs=logs, context=UPSTREAM_CACHE_CONTEXT_NAME)

            entries = {
                "value": response_str,
            }
            if _res_types:
                entries["res_types"] = json.dumps(_res_types)
            log(key=cache_str, context=UPSTREAM_CACHE_CONTEXT_NAME, **entries)
        CACHE_LOCK.release()
    except:
        CACHE_LOCK.release()
        raise Exception(
            f"Failed to write function {fn_name} with kwargs {kw} and "
            f"response {response} to cache at {filename}",
        )


# Decorators #
# -----------#


def cached(
    fn: callable = None,
    *,
    mode: Union[bool, str] = True,
    local: bool = True,
):
    if fn is None:
        return lambda f: cached(
            f,
            mode=mode,
            local=local,
        )

    def wrapped(*args, **kwargs):
        nonlocal mode
        if isinstance(mode, str) and mode.endswith("-closest"):
            mode = mode.removesuffix("-closest")
            read_closest = True
        else:
            read_closest = False
        in_cache = False
        ret = None
        if mode in [True, "both", "read", "read-only"]:
            ret = _get_cache(
                fn_name=fn.__name__,
                kw=kwargs,
                raise_on_empty=mode == "read-only",
                read_closest=read_closest,
                delete_closest=read_closest,
                local=local,
            )
            in_cache = True if ret is not None else False
        if ret is None:
            ret = fn(*args, **kwargs)
        if (ret is not None or read_closest) and mode in [
            True,
            "both",
            "write",
        ]:
            if not in_cache or mode == "write":
                _write_to_cache(
                    fn_name=fn.__name__,
                    kw=kwargs,
                    response=ret,
                    local=local,
                )
        return ret

    return wrapped


# File Manipulation #
# ------------------#


def cache_file_union(
    first_cache_fpath: str,
    second_cache_fpath: str,
    target_cache_fpath: str,
    conflict_mode="raise",
):
    with open(first_cache_fpath, "r") as file:
        first_cache = json.load(file)
    with open(second_cache_fpath, "r") as file:
        second_cache = json.load(file)
    if conflict_mode == "raise":
        for key, value in first_cache.items():
            if key in second_cache:
                assert second_cache[key] == value, (
                    f"key {key} found in both caches, but values conflict:"
                    f"{first_cache_fpath} had value: {value}"
                    f"{second_cache_fpath} had value: {second_cache[key]}"
                )
        union_cache = {**first_cache, **second_cache}
    elif conflict_mode == "first_overrides":
        union_cache = {**second_cache, **first_cache}
    elif conflict_mode == "second_overrides":
        union_cache = {**first_cache, **second_cache}
    else:
        raise Exception(
            "Invalud conflict_mode, must be one of: 'raise', 'first_overrides' or 'second_overrides'",
        )
    with open(target_cache_fpath, "w+") as file:
        json.dump(union_cache, file)


def cache_file_intersection(
    first_cache_fpath: str,
    second_cache_fpath: str,
    target_cache_fpath: str,
    conflict_mode="raise",
):
    with open(first_cache_fpath, "r") as file:
        first_cache = json.load(file)
    with open(second_cache_fpath, "r") as file:
        second_cache = json.load(file)
    if conflict_mode == "raise":
        for key, value in first_cache.items():
            if key in second_cache:
                assert second_cache[key] == value, (
                    f"key {key} found in both caches, but values conflict:"
                    f"{first_cache_fpath} had value: {value}"
                    f"{second_cache_fpath} had value: {second_cache[key]}"
                )
        intersection_cache = {k: v for k, v in first_cache.items() if k in second_cache}
    elif conflict_mode == "first_overrides":
        intersection_cache = {k: v for k, v in first_cache.items() if k in second_cache}
    elif conflict_mode == "second_overrides":
        intersection_cache = {k: v for k, v in second_cache.items() if k in first_cache}
    else:
        raise Exception(
            "Invalud conflict_mode, must be one of: 'raise', 'first_overrides' or 'second_overrides'",
        )
    with open(target_cache_fpath, "w+") as file:
        json.dump(intersection_cache, file)


def subtract_cache_files(
    first_cache_fpath: str,
    second_cache_fpath: str,
    target_cache_fpath: str,
    raise_on_conflict=True,
):
    with open(first_cache_fpath, "r") as file:
        first_cache = json.load(file)
    with open(second_cache_fpath, "r") as file:
        second_cache = json.load(file)
    if raise_on_conflict:
        for key, value in first_cache.items():
            if key in second_cache:
                assert second_cache[key] == value, (
                    f"key {key} found in both caches, but values conflict:"
                    f"{first_cache_fpath} had value: {value}"
                    f"{second_cache_fpath} had value: {second_cache[key]}"
                )
    final_cache = {k: v for k, v in first_cache.items() if k not in second_cache}
    with open(target_cache_fpath, "w+") as file:
        json.dump(final_cache, file)
