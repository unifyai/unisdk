import json
import logging
import os

import requests

_logger = logging.getLogger("unify_requests")
_log_enabled = os.getenv("UNIFY_REQUESTS_DEBUG", "false").lower() in ("true", "1")
_logger.setLevel(logging.DEBUG if _log_enabled else logging.WARNING)


class ResponseDecodeError(Exception):
    def __init__(self, response: requests.Response):
        self.response = response
        super().__init__(f"Request failed to parse response: {response.text}")


class RequestError(Exception):
    def __init__(self, url: str, r_type: str, response: requests.Response, /, **kwargs):
        super().__init__(
            f"{r_type}:{url} with {kwargs} failed with status code {response.status_code}: {response.text}",
        )


def _log(type: str, url: str, mask_key: bool = True, /, **kwargs):
    if not _log_enabled:
        return
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
    _logger.debug(log_msg)


def _mask_auth_key(kwargs: dict):
    if "headers" in kwargs:
        kwargs["headers"]["Authorization"] = "***"
    return kwargs


def request(method, url, **kwargs):
    _log(f"request:{method}", url, True, **kwargs)
    try:
        res = requests.request(method, url, **kwargs)
        res.raise_for_status()
    except requests.exceptions.HTTPError as e:
        kwargs = _mask_auth_key(kwargs)
        raise RequestError(url, method, e.response, **kwargs)

    try:
        _log(f"request:{method} response:{res.status_code}", url, response=res.json())
    except requests.exceptions.JSONDecodeError as e:
        raise ResponseDecodeError(res)
    return res


def get(url, params=None, **kwargs):
    _log("GET", url, True, params=params, **kwargs)
    try:
        res = requests.get(url, params=params, **kwargs)
        res.raise_for_status()
    except requests.exceptions.HTTPError as e:
        kwargs = _mask_auth_key(kwargs)
        raise RequestError(url, "GET", e.response, params=params, **kwargs)

    try:
        _log(f"GET response:{res.status_code}", url, response=res.json())
    except requests.exceptions.JSONDecodeError as e:
        raise ResponseDecodeError(res)
    return res


def options(url, **kwargs):
    _log("OPTIONS", url, True, **kwargs)
    try:
        res = requests.options(url, **kwargs)
        res.raise_for_status()
    except requests.exceptions.HTTPError as e:
        kwargs = _mask_auth_key(kwargs)
        raise RequestError(url, "OPTIONS", e.response, **kwargs)

    try:
        _log(f"OPTIONS response:{res.status_code}", url, response=res.json())
    except requests.exceptions.JSONDecodeError as e:
        raise ResponseDecodeError(res)
    return res


def head(url, **kwargs):
    _log("HEAD", url, True, **kwargs)
    try:
        res = requests.head(url, **kwargs)
    except requests.exceptions.HTTPError as e:
        kwargs = _mask_auth_key(kwargs)
        raise RequestError(url, "HEAD", e.response, **kwargs)

    try:
        _log(f"HEAD response:{res.status_code}", url, response=res.json())
    except requests.exceptions.JSONDecodeError as e:
        raise ResponseDecodeError(res)
    return res


def post(url, data=None, json=None, **kwargs):
    _log("POST", url, True, data=data, json=json, **kwargs)
    try:
        res = requests.post(url, data=data, json=json, **kwargs)
        res.raise_for_status()
    except requests.exceptions.HTTPError as e:
        kwargs = _mask_auth_key(kwargs)
        raise RequestError(url, "POST", e.response, data=data, json=json, **kwargs)

    try:
        _log(f"POST response:{res.status_code}", url, response=res.json())
    except requests.exceptions.JSONDecodeError as e:
        raise ResponseDecodeError(res)
    return res


def put(url, data=None, **kwargs):
    _log("PUT", url, True, data=data, **kwargs)
    try:
        res = requests.put(url, data=data, **kwargs)
        res.raise_for_status()
    except requests.exceptions.HTTPError as e:
        kwargs = _mask_auth_key(kwargs)
        raise RequestError(url, "PUT", e.response, data=data, **kwargs)

    try:
        _log(f"PUT response:{res.status_code}", url, response=res.json())
    except requests.exceptions.JSONDecodeError as e:
        raise ResponseDecodeError(res)
    return res


def patch(url, data=None, **kwargs):
    _log("PATCH", url, True, data=data, **kwargs)
    try:
        res = requests.patch(url, data=data, **kwargs)
        res.raise_for_status()
    except requests.exceptions.HTTPError as e:
        kwargs = _mask_auth_key(kwargs)
        raise RequestError(url, "PATCH", e.response, data=data, **kwargs)

    try:
        _log(f"PATCH response:{res.status_code}", url, response=res.json())
    except requests.exceptions.JSONDecodeError as e:
        raise ResponseDecodeError(res)
    return res


def delete(url, **kwargs):
    _log("DELETE", url, True, **kwargs)
    try:
        res = requests.delete(url, **kwargs)
        res.raise_for_status()
    except requests.exceptions.HTTPError as e:
        kwargs = _mask_auth_key(kwargs)
        raise RequestError(url, "DELETE", e.response, **kwargs)

    try:
        _log(f"DELETE response:{res.status_code}", url, response=res.json())
    except requests.exceptions.JSONDecodeError as e:
        raise ResponseDecodeError(res)
    return res
