"""
HTTP utilities for the Unify SDK.

Provides a requests session with retry logic and optional trace-aware logging.

Logging is controlled by two environment variables:
- UNIFY_LOG: Enable/disable logging (default: true)
- UNIFY_LOG_DIR: Directory for log files (default: console only)

When UNIFY_LOG_DIR is set, structured JSON files are written:
- Before request: {timestamp}_{method}_{route}_PENDING_{trace_id}.json
- After response: {timestamp}_{method}_{route}_{duration}ms_{status}_{trace_id}.json

The trace_id suffix enables correlation with pytest logs and Orchestra traces.
"""

import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

# ---------------------------------------------------------------------------
# Console logging setup
# ---------------------------------------------------------------------------

_LOGGER = logging.getLogger("unify")
_LOG_ENABLED = os.getenv("UNIFY_LOG", "true").lower() in ("true", "1")
_LOGGER.setLevel(logging.DEBUG if _LOG_ENABLED else logging.WARNING)

# ---------------------------------------------------------------------------
# File-based trace logging
# ---------------------------------------------------------------------------

_LOG_DIR: Optional[Path] = None
_LOG_DIR_CHECKED = False


def configure_log_dir(log_dir: Optional[str] = None) -> Optional[Path]:
    """Configure or reconfigure the log directory for file-based logging.

    Call this after setting UNIFY_LOG_DIR if the env var was set
    after this module was imported.

    Args:
        log_dir: Explicit log directory path. If None, reads from
                 UNIFY_LOG_DIR env var.

    Returns:
        The configured log directory Path, or None if disabled.
    """
    global _LOG_DIR, _LOG_DIR_CHECKED

    _LOG_DIR_CHECKED = False
    _LOG_DIR = None

    if log_dir is not None:
        os.environ["UNIFY_LOG_DIR"] = log_dir

    return _get_log_dir()


def _get_log_dir() -> Optional[Path]:
    """Get the log directory from UNIFY_LOG_DIR env var.

    Returns None if not set or directory creation fails.
    The directory is created on first access.
    """
    global _LOG_DIR, _LOG_DIR_CHECKED

    if _LOG_DIR_CHECKED:
        return _LOG_DIR

    _LOG_DIR_CHECKED = True
    log_dir_str = os.getenv("UNIFY_LOG_DIR", "").strip()
    if not log_dir_str:
        return None

    try:
        log_dir = Path(log_dir_str)
        log_dir.mkdir(parents=True, exist_ok=True)
        _LOG_DIR = log_dir
        _LOGGER.debug(f"HTTP trace logging enabled: {log_dir}")
    except Exception as e:
        _LOGGER.warning(f"Failed to create HTTP log directory {log_dir_str}: {e}")
        _LOG_DIR = None

    return _LOG_DIR


def _get_current_trace_id() -> Optional[str]:
    """Extract the current OpenTelemetry trace_id if available.

    Returns a 32-character hex string, or None if no active span.
    """
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span is None:
            return None
        ctx = span.get_span_context()
        if ctx is not None and ctx.is_valid:
            return f"{ctx.trace_id:032x}"
    except Exception:
        pass
    return None


def _extract_route(url: str) -> str:
    """Extract a safe route identifier from a URL for use in filenames.

    Examples:
        https://api.unify.ai/v0/logs -> logs
        https://api.unify.ai/v0/logs/derived -> logs-derived
        https://api.unify.ai/v0/project/foo/contexts -> project-contexts
    """
    try:
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        # Remove version prefix (v0/, v1/, etc.)
        path = re.sub(r"^v\d+/", "", path)
        # Replace path separators and collapse multiple dashes
        route = re.sub(r"[/]+", "-", path)
        route = re.sub(r"-+", "-", route)
        # Limit length and remove unsafe chars
        route = re.sub(r"[^a-zA-Z0-9_-]", "", route)[:30]
        return route or "unknown"
    except Exception:
        return "unknown"


def _mask_headers(headers: Optional[dict]) -> Optional[dict]:
    """Return a copy of headers with Authorization masked."""
    if not headers:
        return headers
    masked = dict(headers)
    if "Authorization" in masked:
        masked["Authorization"] = "***"
    if "authorization" in masked:
        masked["authorization"] = "***"
    return masked


def _write_pending_trace(
    method: str,
    url: str,
    request_kwargs: dict,
) -> Optional[Path]:
    """Write a pending trace file before the request is made.

    Returns the file path for later finalization, or None if logging disabled.
    """
    log_dir = _get_log_dir()
    if log_dir is None:
        return None

    try:
        trace_id = _get_current_trace_id()
        trace_suffix = trace_id[-8:] if trace_id else "no-trace"
        route = _extract_route(url)

        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%H-%M-%S.") + f"{now.microsecond // 1000:03d}"

        filename = f"{timestamp}_{method}_{route}_PENDING_{trace_suffix}.json"
        filepath = log_dir / filename

        # Build the trace record
        record = {
            "timestamp": now.isoformat(),
            "trace_id": trace_id,
            "method": method,
            "url": url,
            "route": route,
            "status": "pending",
            "request": {
                "headers": _mask_headers(request_kwargs.get("headers")),
                "params": request_kwargs.get("params"),
                "json": request_kwargs.get("json"),
                "data": (
                    str(request_kwargs.get("data"))[:1000]
                    if request_kwargs.get("data")
                    else None
                ),
            },
        }

        with filepath.open("w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, default=str)

        return filepath
    except Exception as e:
        _LOGGER.debug(f"Failed to write pending trace: {e}")
        return None


def _finalize_trace(
    pending_path: Optional[Path],
    response: requests.Response,
    duration_ms: int,
) -> None:
    """Finalize a pending trace file with response data.

    Renames the file from _PENDING_ to _{duration}ms_{status}_.
    """
    if pending_path is None or not pending_path.exists():
        return

    try:
        # Read existing record
        with pending_path.open("r", encoding="utf-8") as f:
            record = json.load(f)

        # Add response data
        record["status"] = "complete"
        record["duration_ms"] = duration_ms
        record["response"] = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
        }

        # Try to include response body (truncated for large responses)
        try:
            body = response.json()
            # Truncate large responses
            body_str = json.dumps(body)
            if len(body_str) > 10000:
                record["response"]["body"] = "(truncated, >10KB)"
                record["response"]["body_preview"] = body_str[:1000]
            else:
                record["response"]["body"] = body
        except Exception:
            text = response.text
            if len(text) > 1000:
                record["response"]["body"] = text[:1000] + "...(truncated)"
            else:
                record["response"]["body"] = text

        # Write updated record
        with pending_path.open("w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, default=str)

        # Rename file to reflect completion
        new_name = pending_path.name.replace(
            "_PENDING_",
            f"_{duration_ms}ms_{response.status_code}_",
        )
        new_path = pending_path.parent / new_name
        pending_path.rename(new_path)

    except Exception as e:
        _LOGGER.debug(f"Failed to finalize trace: {e}")


def _mark_trace_failed(
    pending_path: Optional[Path],
    error: Exception,
    duration_ms: int,
) -> None:
    """Mark a pending trace as failed due to an exception."""
    if pending_path is None or not pending_path.exists():
        return

    try:
        with pending_path.open("r", encoding="utf-8") as f:
            record = json.load(f)

        record["status"] = "failed"
        record["duration_ms"] = duration_ms
        record["error"] = {
            "type": type(error).__name__,
            "message": str(error),
        }

        with pending_path.open("w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, default=str)

        # Rename to indicate failure
        new_name = pending_path.name.replace("_PENDING_", f"_{duration_ms}ms_FAILED_")
        new_path = pending_path.parent / new_name
        pending_path.rename(new_path)

    except Exception as e:
        _LOGGER.debug(f"Failed to mark trace as failed: {e}")


# ---------------------------------------------------------------------------
# Session configuration
# ---------------------------------------------------------------------------

_SESSION = requests.Session()
_RETRIES = Retry(
    total=5,
    connect=3,
    read=2,
    backoff_factor=0.1,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=None,  # Retry all methods including POST
)
_ADAPTER = HTTPAdapter(max_retries=_RETRIES, pool_connections=20, pool_maxsize=20)
_SESSION.mount("http://", _ADAPTER)
_SESSION.mount("https://", _ADAPTER)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class RequestError(Exception):
    def __init__(self, url: str, r_type: str, response: requests.Response, /, **kwargs):
        super().__init__(
            f"{r_type}:{url} with {kwargs} failed with status code "
            f"{response.status_code}: {response.text}",
        )
        self.response = response


def _log_to_console(log_type: str, url: str, mask_key: bool = True, /, **kwargs):
    """Log request/response details to the console logger."""
    kwargs_str = ""
    safe_kwargs = dict(kwargs)

    if mask_key and "headers" in safe_kwargs:
        safe_kwargs["headers"] = _mask_headers(safe_kwargs["headers"])

    for k, v in safe_kwargs.items():
        if isinstance(v, dict):
            kwargs_str += f"{k}:{json.dumps(v, indent=2)},\n"
        else:
            kwargs_str += f"{k}:{v},\n"

    trace_id = _get_current_trace_id()
    trace_prefix = f"[{trace_id[-8:]}] " if trace_id else ""

    log_msg = f"""
{trace_prefix}====== {log_type} =======
url:{url}
{kwargs_str}
"""
    _LOGGER.debug(log_msg)


def _mask_auth_key(kwargs: dict) -> dict:
    """Return a sanitized copy of request kwargs suitable for error messages.

    IMPORTANT: This must NOT mutate caller-owned objects (e.g. the headers dict),
    because higher-level callers may reuse those objects across multiple HTTP
    calls (e.g. in loops).
    """
    if "headers" not in kwargs:
        return kwargs

    headers = kwargs.get("headers")
    if not isinstance(headers, dict):
        return kwargs

    safe_kwargs = dict(kwargs)
    safe_kwargs["headers"] = _mask_headers(headers)
    return safe_kwargs


def _log_request_if_enabled(fn: Callable) -> Callable:
    """Decorator that adds console and file-based logging to requests."""
    if not _LOG_ENABLED:
        return fn

    @wraps(fn)
    def inner(method: str, url: str, **kwargs) -> requests.Response:
        # Console log: request
        _log_to_console(f"{method}", url, True, **kwargs)

        # File trace: pending
        pending_path = _write_pending_trace(method, url, kwargs)

        start_time = time.monotonic()
        try:
            res: requests.Response = fn(method, url, **kwargs)
            duration_ms = int((time.monotonic() - start_time) * 1000)

            # Console log: response
            try:
                _log_to_console(
                    f"{method} response:{res.status_code}",
                    url,
                    response=res.json(),
                )
            except requests.exceptions.JSONDecodeError:
                _log_to_console(
                    f"{method} response:{res.status_code}",
                    url,
                    response=res.text[:500] if res.text else "(empty)",
                )

            # File trace: finalize
            _finalize_trace(pending_path, res, duration_ms)

            return res

        except Exception as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            _mark_trace_failed(pending_path, e, duration_ms)
            raise

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
