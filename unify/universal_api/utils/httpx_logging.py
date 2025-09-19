import json
import os
from typing import Optional
from urllib.parse import urlparse

import httpx


def _unify_requests_debug_enabled() -> bool:
    return os.getenv("UNIFY_REQUESTS_DEBUG", "false").lower() in ("true", "1")


def make_httpx_client_for_unify_logging(base_url: str) -> Optional[httpx.Client]:
    if not _unify_requests_debug_enabled():
        return None

    from unify.utils import http as _unify_requests

    parsed = urlparse(base_url)
    base_host = parsed.hostname
    base_scheme = parsed.scheme

    def _is_unify_chat_request(request: httpx.Request) -> bool:
        try:
            if request.url.host != base_host or request.url.scheme != base_scheme:
                return False
            return request.url.path.endswith("/chat/completions")
        except Exception:
            return False

    def _pre_request_log(request: httpx.Request) -> None:
        try:
            if not _is_unify_chat_request(request):
                return
            method = request.method.upper()
            url_str = str(request.url)

            headers = dict(request.headers)
            # normalize Authorization header key for masking in http._log
            auth_val = headers.get("Authorization", headers.get("authorization"))
            if auth_val is not None:
                headers["Authorization"] = auth_val
                if "authorization" in headers:
                    try:
                        del headers["authorization"]
                    except Exception:
                        pass
            params = dict(request.url.params)
            body_json = None
            if request.content:
                try:
                    body_json = json.loads(
                        (
                            request.content.decode("utf-8")
                            if isinstance(request.content, (bytes, bytearray))
                            else request.content
                        ),
                    )
                except Exception:
                    body_json = None

            kw = {"headers": headers}
            if params:
                kw["params"] = params
            if body_json is not None:
                kw["json"] = body_json

            _unify_requests._log(method, url_str, True, **kw)
        except Exception:
            pass

    def _post_response_log(response: httpx.Response) -> None:
        try:
            request = response.request
            if not _is_unify_chat_request(request):
                return
            method = request.method.upper()
            url_str = str(request.url)

            is_stream = False
            try:
                req_body = None
                if request.content:
                    try:
                        req_body = json.loads(
                            (
                                request.content.decode("utf-8")
                                if isinstance(request.content, (bytes, bytearray))
                                else request.content
                            ),
                        )
                    except Exception:
                        req_body = None
                if isinstance(req_body, dict) and req_body.get("stream") is True:
                    is_stream = True
                if "text/event-stream" in (
                    response.headers.get("content-type", "").lower()
                ):
                    is_stream = True
            except Exception:
                pass

            if is_stream:
                _unify_requests._log(
                    f"{method} response:{response.status_code}",
                    url_str,
                    True,
                    response={},
                )
                return

            try:
                response.read()
            except Exception:
                pass
            try:
                payload = response.json()
            except Exception:
                return
            _unify_requests._log(
                f"{method} response:{response.status_code}",
                url_str,
                response=payload,
            )
        except Exception:
            pass

    return httpx.Client(
        event_hooks={"request": [_pre_request_log], "response": [_post_response_log]},
    )


def make_async_httpx_client_for_unify_logging(
    base_url: str,
) -> Optional[httpx.AsyncClient]:
    if not _unify_requests_debug_enabled():
        return None

    from unify.utils import http as _unify_requests

    parsed = urlparse(base_url)
    base_host = parsed.hostname
    base_scheme = parsed.scheme

    def _is_unify_chat_request(request: httpx.Request) -> bool:
        try:
            if request.url.host != base_host or request.url.scheme != base_scheme:
                return False
            return request.url.path.endswith("/chat/completions")
        except Exception:
            return False

    async def _pre_request_log(request: httpx.Request) -> None:
        try:
            if not _is_unify_chat_request(request):
                return
            method = request.method.upper()
            url_str = str(request.url)

            headers = dict(request.headers)
            auth_val = headers.get("Authorization", headers.get("authorization"))
            if auth_val is not None:
                headers["Authorization"] = auth_val
                if "authorization" in headers:
                    try:
                        del headers["authorization"]
                    except Exception:
                        pass
            params = dict(request.url.params)
            body_json = None
            if request.content:
                try:
                    body_json = json.loads(
                        (
                            request.content.decode("utf-8")
                            if isinstance(request.content, (bytes, bytearray))
                            else request.content
                        ),
                    )
                except Exception:
                    body_json = None

            kw = {"headers": headers}
            if params:
                kw["params"] = params
            if body_json is not None:
                kw["json"] = body_json

            _unify_requests._log(method, url_str, True, **kw)
        except Exception:
            pass

    async def _post_response_log(response: httpx.Response) -> None:
        try:
            request = response.request
            if not _is_unify_chat_request(request):
                return
            method = request.method.upper()
            url_str = str(request.url)

            is_stream = False
            try:
                req_body = None
                if request.content:
                    try:
                        req_body = json.loads(
                            (
                                request.content.decode("utf-8")
                                if isinstance(request.content, (bytes, bytearray))
                                else request.content
                            ),
                        )
                    except Exception:
                        req_body = None
                if isinstance(req_body, dict) and req_body.get("stream") is True:
                    is_stream = True
                if "text/event-stream" in (
                    response.headers.get("content-type", "").lower()
                ):
                    is_stream = True
            except Exception:
                pass

            if is_stream:
                _unify_requests._log(
                    f"{method} response:{response.status_code}",
                    url_str,
                    True,
                    response={},
                )
                return

            try:
                await response.aread()
            except Exception:
                pass
            try:
                payload = response.json()
            except Exception:
                return
            _unify_requests._log(
                f"{method} response:{response.status_code}",
                url_str,
                response=payload,
            )
        except Exception:
            pass

    return httpx.AsyncClient(
        event_hooks={"request": [_pre_request_log], "response": [_post_response_log]},
    )
