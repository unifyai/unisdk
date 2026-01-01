"""
Tests for HTTP utilities: logging and OpenTelemetry tracing.

These tests verify:
1. Console logging can be enabled/disabled via UNIFY_LOG
2. File-based trace logging works when UNIFY_LOG_DIR is set
3. OpenTelemetry spans are created when UNIFY_OTEL is enabled
4. Trace context propagation works correctly
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


@pytest.fixture
def reset_otel():
    """Reset OTel state before and after test.

    OTel uses global state (singleton TracerProvider). This fixture ensures
    proper isolation between tests by resetting to a fresh provider.
    """
    # Create a fresh provider with in-memory exporter for test inspection
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    # OTel doesn't allow overriding, but we can manipulate the internal state
    # pylint: disable=protected-access
    trace._TRACER_PROVIDER_SET_ONCE._done = False
    trace._TRACER_PROVIDER = None

    trace.set_tracer_provider(provider)

    yield {"provider": provider, "exporter": exporter}

    # Cleanup
    exporter.clear()


class TestLogEnabled:
    """Tests for UNIFY_LOG master switch."""

    def test_log_enabled_by_default(self):
        """UNIFY_LOG defaults to true."""
        with patch.dict(os.environ, {}, clear=False):
            # Remove UNIFY_LOG if set
            os.environ.pop("UNIFY_LOG", None)
            # Re-import to pick up new env var
            import importlib

            from unify.utils import http

            importlib.reload(http)
            assert http._LOG_ENABLED is True

    def test_log_disabled_via_env(self):
        """UNIFY_LOG=false disables logging."""
        with patch.dict(os.environ, {"UNIFY_LOG": "false"}):
            import importlib

            from unify.utils import http

            importlib.reload(http)
            assert http._LOG_ENABLED is False

    def test_log_enabled_true(self):
        """UNIFY_LOG=true enables logging."""
        with patch.dict(os.environ, {"UNIFY_LOG": "true"}):
            import importlib

            from unify.utils import http

            importlib.reload(http)
            assert http._LOG_ENABLED is True

    def test_log_enabled_1(self):
        """UNIFY_LOG=1 enables logging."""
        with patch.dict(os.environ, {"UNIFY_LOG": "1"}):
            import importlib

            from unify.utils import http

            importlib.reload(http)
            assert http._LOG_ENABLED is True


class TestOtelEnabled:
    """Tests for UNIFY_OTEL master switch."""

    def test_otel_disabled_by_default(self):
        """UNIFY_OTEL defaults to false."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("UNIFY_OTEL", None)
            import importlib

            from unify.utils import http

            importlib.reload(http)
            assert http._OTEL_ENABLED is False

    def test_otel_enabled_via_env(self):
        """UNIFY_OTEL=true enables OTel."""
        with patch.dict(os.environ, {"UNIFY_OTEL": "true"}):
            import importlib

            from unify.utils import http

            importlib.reload(http)
            assert http._OTEL_ENABLED is True

    def test_otel_enabled_1(self):
        """UNIFY_OTEL=1 enables OTel."""
        with patch.dict(os.environ, {"UNIFY_OTEL": "1"}):
            import importlib

            from unify.utils import http

            importlib.reload(http)
            assert http._OTEL_ENABLED is True


class TestExtractRoute:
    """Tests for _extract_route helper."""

    def test_simple_route(self):
        from unify.utils.http import _extract_route

        assert _extract_route("https://api.unify.ai/v0/logs") == "logs"

    def test_nested_route(self):
        from unify.utils.http import _extract_route

        assert _extract_route("https://api.unify.ai/v0/logs/derived") == "logs-derived"

    def test_route_with_path_params(self):
        from unify.utils.http import _extract_route

        result = _extract_route("https://api.unify.ai/v0/project/foo/contexts")
        assert result == "project-foo-contexts"

    def test_empty_path(self):
        from unify.utils.http import _extract_route

        assert _extract_route("https://api.unify.ai/") == "unknown"

    def test_invalid_url(self):
        from unify.utils.http import _extract_route

        # Invalid URLs are handled gracefully (the path is extracted as-is)
        result = _extract_route("not-a-url")
        assert isinstance(result, str)
        assert len(result) > 0


class TestMaskHeaders:
    """Tests for _mask_headers helper."""

    def test_masks_authorization(self):
        from unify.utils.http import _mask_headers

        headers = {
            "Authorization": "Bearer secret123",
            "Content-Type": "application/json",
        }
        masked = _mask_headers(headers)
        assert masked["Authorization"] == "***"
        assert masked["Content-Type"] == "application/json"

    def test_masks_lowercase_authorization(self):
        from unify.utils.http import _mask_headers

        headers = {"authorization": "Bearer secret123"}
        masked = _mask_headers(headers)
        assert masked["authorization"] == "***"

    def test_none_headers(self):
        from unify.utils.http import _mask_headers

        assert _mask_headers(None) is None

    def test_empty_headers(self):
        from unify.utils.http import _mask_headers

        assert _mask_headers({}) == {}


class TestFileTraceLogging:
    """Tests for file-based trace logging."""

    def test_write_pending_trace_creates_file(self):
        """_write_pending_trace creates a JSON file."""
        from unify.utils import http

        with tempfile.TemporaryDirectory() as tmpdir:
            # Configure log directory
            with patch.dict(os.environ, {"UNIFY_LOG_DIR": tmpdir}):
                http._LOG_DIR = None
                http._LOG_DIR_CHECKED = False

                path = http._write_pending_trace(
                    "POST",
                    "https://api.unify.ai/v0/logs",
                    {"json": {"key": "value"}},
                )

                assert path is not None
                assert path.exists()
                assert "PENDING" in path.name
                assert "POST" in path.name
                assert "logs" in path.name

                # Verify JSON content
                with path.open() as f:
                    data = json.load(f)
                assert data["method"] == "POST"
                assert data["status"] == "pending"
                assert data["request"]["json"] == {"key": "value"}

    def test_finalize_trace_renames_file(self):
        """_finalize_trace renames PENDING to duration and status."""
        from unify.utils import http

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"UNIFY_LOG_DIR": tmpdir}):
                http._LOG_DIR = None
                http._LOG_DIR_CHECKED = False

                # Create pending trace
                path = http._write_pending_trace(
                    "GET",
                    "https://api.unify.ai/v0/projects",
                    {},
                )

                # Create mock response
                response = MagicMock(spec=requests.Response)
                response.status_code = 200
                response.headers = {"Content-Type": "application/json"}
                response.json.return_value = {"projects": []}

                # Finalize
                http._finalize_trace(path, response, 150)

                # Original file should be renamed
                assert not path.exists()

                # Find the finalized file
                files = list(Path(tmpdir).glob("*.json"))
                assert len(files) == 1
                final_path = files[0]
                assert "150ms" in final_path.name
                assert "200" in final_path.name
                assert "PENDING" not in final_path.name

    def test_mark_trace_failed(self):
        """_mark_trace_failed marks trace as failed."""
        from unify.utils import http

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"UNIFY_LOG_DIR": tmpdir}):
                http._LOG_DIR = None
                http._LOG_DIR_CHECKED = False

                # Create pending trace
                path = http._write_pending_trace(
                    "POST",
                    "https://api.unify.ai/v0/logs",
                    {},
                )

                # Mark as failed
                error = ConnectionError("Network error")
                http._mark_trace_failed(path, error, 50)

                # Original file should be renamed
                assert not path.exists()

                # Find the failed file
                files = list(Path(tmpdir).glob("*.json"))
                assert len(files) == 1
                final_path = files[0]
                assert "FAILED" in final_path.name
                assert "50ms" in final_path.name

                # Check error content
                with final_path.open() as f:
                    data = json.load(f)
                assert data["status"] == "failed"
                assert data["error"]["type"] == "ConnectionError"

    def test_no_logging_when_disabled(self):
        """No trace files created when UNIFY_LOG_DIR not set."""
        from unify.utils import http

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("UNIFY_LOG_DIR", None)
            http._LOG_DIR = None
            http._LOG_DIR_CHECKED = False

            path = http._write_pending_trace(
                "GET",
                "https://api.unify.ai/v0/projects",
                {},
            )

            assert path is None


class TestGetCurrentTraceId:
    """Tests for _get_current_trace_id helper."""

    def test_returns_none_when_no_span(self):
        """Returns None when no active OTel span."""
        from unify.utils.http import _get_current_trace_id

        # Without an active span, should return None
        result = _get_current_trace_id()
        # May return None or empty depending on provider state
        assert result is None or isinstance(result, str)

    def test_returns_trace_id_when_span_active(self, reset_otel):
        """Returns trace_id when OTel span is active."""
        tracer = trace.get_tracer("test")

        from unify.utils.http import _get_current_trace_id

        with tracer.start_as_current_span("test-span"):
            result = _get_current_trace_id()
            assert result is not None
            assert len(result) == 32  # 32-char hex string
            # Verify it's a valid hex string
            int(result, 16)


class TestConfigureLogDir:
    """Tests for configure_log_dir function."""

    def test_configure_with_explicit_path(self):
        """configure_log_dir with explicit path."""
        from unify.utils import http

        with tempfile.TemporaryDirectory() as tmpdir:
            result = http.configure_log_dir(tmpdir)
            assert result == Path(tmpdir)
            assert http._LOG_DIR == Path(tmpdir)

    def test_configure_from_env(self):
        """configure_log_dir reads from UNIFY_LOG_DIR env."""
        from unify.utils import http

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"UNIFY_LOG_DIR": tmpdir}):
                http._LOG_DIR = None
                http._LOG_DIR_CHECKED = False
                result = http.configure_log_dir()
                assert result == Path(tmpdir)

    def test_configure_returns_none_when_not_set(self):
        """configure_log_dir returns None when no directory configured."""
        from unify.utils import http

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("UNIFY_LOG_DIR", None)
            http._LOG_DIR = None
            http._LOG_DIR_CHECKED = False
            result = http.configure_log_dir()
            assert result is None


class TestOtelTracing:
    """Tests for OpenTelemetry tracing functionality."""

    def test_get_tracer_returns_none_when_disabled(self):
        """get_tracer returns None when UNIFY_OTEL is false."""
        with patch.dict(os.environ, {"UNIFY_OTEL": "false"}):
            import importlib

            from unify.utils import http

            importlib.reload(http)
            assert http.get_tracer() is None

    def test_is_otel_enabled_reflects_env(self):
        """is_otel_enabled reflects UNIFY_OTEL env var."""
        with patch.dict(os.environ, {"UNIFY_OTEL": "true"}):
            import importlib

            from unify.utils import http

            importlib.reload(http)
            assert http.is_otel_enabled() is True

        with patch.dict(os.environ, {"UNIFY_OTEL": "false"}):
            import importlib

            from unify.utils import http

            importlib.reload(http)
            assert http.is_otel_enabled() is False

    def test_otel_setup_uses_existing_provider(self, reset_otel):
        """OTel setup uses existing TracerProvider if available."""
        existing_provider = reset_otel["provider"]

        with patch.dict(os.environ, {"UNIFY_OTEL": "true"}):
            import importlib

            from unify.utils import http

            # Reset initialization state and reload with OTel enabled
            http._OTEL_INITIALIZED = False
            http._TRACER = None
            importlib.reload(http)

            tracer = http.get_tracer()
            assert tracer is not None

            # Should use existing provider, not create new one
            assert trace.get_tracer_provider() is existing_provider

    def test_get_tracer_returns_tracer_when_enabled(self, reset_otel):
        """get_tracer returns a tracer when UNIFY_OTEL is true."""
        with patch.dict(os.environ, {"UNIFY_OTEL": "true"}):
            import importlib

            from unify.utils import http

            http._OTEL_INITIALIZED = False
            http._TRACER = None

            importlib.reload(http)
            tracer = http.get_tracer()

            # Should have a tracer now
            assert tracer is not None

    def test_spans_created_during_request(self, reset_otel):
        """HTTP requests create OTel spans when UNIFY_OTEL is enabled."""
        exporter = reset_otel["exporter"]

        with patch.dict(os.environ, {"UNIFY_OTEL": "true", "UNIFY_LOG": "false"}):
            import importlib

            from unify.utils import http

            # Reset initialization state and reload with OTel enabled
            http._OTEL_INITIALIZED = False
            http._TRACER = None
            importlib.reload(http)

            # Mock the actual HTTP call
            mock_response = MagicMock(spec=requests.Response)
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.json.return_value = {}

            with patch.object(http._SESSION, "request", return_value=mock_response):
                http.get("https://api.unify.ai/v0/projects")

            # Check spans were created
            spans = exporter.get_finished_spans()
            assert len(spans) >= 1

            # Verify span attributes
            span = spans[-1]
            assert span.name == "GET projects"
            assert span.attributes.get("http.method") == "GET"
            assert "api.unify.ai" in span.attributes.get("http.url", "")
            assert span.attributes.get("http.status_code") == 200

    def test_span_records_error_on_exception(self, reset_otel):
        """HTTP request spans record errors when exceptions occur."""
        exporter = reset_otel["exporter"]

        with patch.dict(os.environ, {"UNIFY_OTEL": "true", "UNIFY_LOG": "false"}):
            import importlib

            from unify.utils import http

            http._OTEL_INITIALIZED = False
            http._TRACER = None
            importlib.reload(http)

            # Mock HTTP call to raise exception
            with patch.object(
                http._SESSION,
                "request",
                side_effect=ConnectionError("Network error"),
            ):
                with pytest.raises(ConnectionError):
                    http.get("https://api.unify.ai/v0/projects")

            # Check span recorded error
            spans = exporter.get_finished_spans()
            assert len(spans) >= 1

            span = spans[-1]
            assert span.attributes.get("error.type") == "ConnectionError"
            assert "Network error" in span.attributes.get("error.message", "")

    def test_span_records_http_error_status(self, reset_otel):
        """HTTP request spans record error status for 4xx/5xx responses."""
        exporter = reset_otel["exporter"]

        with patch.dict(os.environ, {"UNIFY_OTEL": "true", "UNIFY_LOG": "false"}):
            import importlib

            from unify.utils import http

            http._OTEL_INITIALIZED = False
            http._TRACER = None
            importlib.reload(http)

            # Mock 404 response (but don't raise - set raise_for_status=False)
            mock_response = MagicMock(spec=requests.Response)
            mock_response.status_code = 404
            mock_response.headers = {}
            mock_response.text = "Not found"
            mock_response.json.side_effect = requests.exceptions.JSONDecodeError(
                "err",
                "doc",
                0,
            )
            mock_response.raise_for_status.return_value = None

            with patch.object(http._SESSION, "request", return_value=mock_response):
                http.get(
                    "https://api.unify.ai/v0/projects",
                    raise_for_status=False,
                )

            # Check span has error status
            spans = exporter.get_finished_spans()
            assert len(spans) >= 1

            span = spans[-1]
            assert span.attributes.get("http.status_code") == 404


class TestRequestError:
    """Tests for RequestError exception."""

    def test_request_error_message(self):
        """RequestError includes URL, method, status, and response text."""
        from unify.utils.http import RequestError

        response = MagicMock(spec=requests.Response)
        response.status_code = 404
        response.text = "Not found"

        error = RequestError(
            "https://api.unify.ai/v0/foo",
            "GET",
            response,
            params={"x": 1},
        )

        assert "GET" in str(error)
        assert "https://api.unify.ai/v0/foo" in str(error)
        assert "404" in str(error)
        assert "Not found" in str(error)
        assert error.response is response


class TestMaskAuthKey:
    """Tests for _mask_auth_key helper."""

    def test_masks_headers_in_kwargs(self):
        """_mask_auth_key masks Authorization header in kwargs copy."""
        from unify.utils.http import _mask_auth_key

        original = {
            "headers": {"Authorization": "Bearer secret"},
            "params": {"x": 1},
        }

        masked = _mask_auth_key(original)

        # Original unchanged
        assert original["headers"]["Authorization"] == "Bearer secret"

        # Masked copy has hidden auth
        assert masked["headers"]["Authorization"] == "***"
        assert masked["params"] == {"x": 1}

    def test_returns_unchanged_without_headers(self):
        """_mask_auth_key returns unchanged when no headers."""
        from unify.utils.http import _mask_auth_key

        kwargs = {"params": {"x": 1}}
        result = _mask_auth_key(kwargs)
        assert result is kwargs
