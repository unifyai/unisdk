import json
import logging
import os
from functools import wraps
from typing import Callable

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

_LOGGER = logging.getLogger("unify_requests")
_LOG_ENABLED = os.getenv("UNIFY_REQUESTS_DEBUG", "false").lower() in ("true", "1")
_LOGGER.setLevel(logging.DEBUG if _LOG_ENABLED else logging.WARNING)

_SESSION = requests.Session()
_RETRIES = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
_ADAPTER = HTTPAdapter(max_retries=_RETRIES, pool_connections=20, pool_maxsize=20)
_SESSION.mount("http://", _ADAPTER)
_SESSION.mount("https://", _ADAPTER)


class RequestError(Exception):
    def __init__(self, url: str, r_type: str, response: requests.Response, /, **kwargs):
        super().__init__(
            f"{r_type}:{url} with {kwargs} failed with status code {response.status_code}: {response.text}",
        )
        self.response = response


def _log(type: str, url: str, mask_key: bool = True, /, **kwargs):
    _kwargs_str = ""
    if mask_key and "headers" in kwargs:
        key = kwargs["headers"]["Authorization"]
        kwargs["headers"]["Authorization"] = "***"

    for k, v in kwargs.items():
        if isinstance(v, dict):
            _kwargs_str += f"{k:}:{json.dumps(v, indent=2)},\n"
        else:
            _kwargs_str += f"{k}:{v},\n"

    if mask_key and "headers" in kwargs:
        kwargs["headers"]["Authorization"] = key

    log_msg = f"""
====== {type} =======
url:{url}
{_kwargs_str}
"""
    _LOGGER.debug(log_msg)


def _mask_auth_key(kwargs: dict):
    if "headers" in kwargs:
        kwargs["headers"]["Authorization"] = "***"
    return kwargs


def _log_request_if_enabled(fn: Callable) -> Callable:
    """
    Only wrap request function if logging is enabled.
    """
    if not _LOG_ENABLED:
        return fn

    @wraps(fn)
    def inner(method, url, **kwargs):
        _log(f"{method}", url, True, **kwargs)
        res: requests.Response = fn(method, url, **kwargs)
        try:
            _log(f"{method} response:{res.status_code}", url, response=res.json())
        except requests.exceptions.JSONDecodeError:
            _log(f"{method} response:{res.status_code}", url, response=res.text)
        return res

    return inner


@_log_request_if_enabled
def request(method, url, raise_for_status=True, **kwargs) -> requests.Response:
    try:
        res = _SESSION.request(method, url, **kwargs)
        if raise_for_status:
            res.raise_for_status()
        return res
    except requests.exceptions.HTTPError as e:
        kwargs = _mask_auth_key(kwargs)
        raise RequestError(url, method, e.response, **kwargs)


def get(url, params=None, **kwargs):
    return request("GET", url, params=params, **kwargs)


def options(url, **kwargs):
    return request("OPTIONS", url, **kwargs)


def head(url, **kwargs):
    return request("HEAD", url, **kwargs)


def post(url, data=None, json=None, **kwargs):
    return request("POST", url, data=data, json=json, **kwargs)


def put(url, data=None, **kwargs):
    return request("PUT", url, data=data, **kwargs)


def patch(url, data=None, **kwargs):
    return request("PATCH", url, data=data, **kwargs)


def delete(url, **kwargs):
    return request("DELETE", url, **kwargs)
