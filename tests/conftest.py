# Load .env BEFORE importing unify - BASE_URL is evaluated at import time.
# Explicit shell environment variables take precedence over .env values.
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Look for .env in repo root (parent of tests/)
_repo_root = Path(__file__).resolve().parent.parent
load_dotenv(_repo_root / ".env", override=False)

import pytest

# ---------------------------------------------------------------------------
# Log directory configuration
# ---------------------------------------------------------------------------


def _get_log_subdir() -> str:
    """Generate a datetime-prefixed subdirectory name for log isolation."""
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    # Use a simple identifier (PID) for this repo
    return f"{timestamp}_unifypid{os.getpid()}"


def pytest_sessionstart(session):
    """Configure all file-based logging directories for trace correlation."""
    root_path = Path(session.config.rootpath)
    subdir = _get_log_subdir()

    # Unify SDK file logging (HTTP request traces)
    unify_log_dir = root_path / "logs" / "unify" / subdir
    unify_log_dir.mkdir(parents=True, exist_ok=True)
    try:
        from unify.utils.http import configure_log_dir as configure_unify_log_dir

        configure_unify_log_dir(str(unify_log_dir))
    except ImportError:
        os.environ["UNIFY_LOG_DIR"] = str(unify_log_dir)

    # Orchestra log directory (for local orchestra server, if running)
    # This sets the env var so that if a local orchestra is started, it knows where to log
    orchestra_log_dir = root_path / "logs" / "orchestra" / subdir
    orchestra_log_dir.mkdir(parents=True, exist_ok=True)
    os.environ["ORCHESTRA_LOG_DIR"] = str(orchestra_log_dir)

    # Cross-repo OTEL traces (all services write to the same directory)
    otel_log_dir = root_path / "logs" / "all" / subdir
    otel_log_dir.mkdir(parents=True, exist_ok=True)
    os.environ["UNIFY_OTEL_LOG_DIR"] = str(otel_log_dir)
    os.environ["ORCHESTRA_OTEL_LOG_DIR"] = str(otel_log_dir)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


# ---------------------------------------------------------------------------
# Orchestra reachability gate
# ---------------------------------------------------------------------------
#
# The integration test suite assumes an Orchestra backend is reachable at
# ORCHESTRA_URL (or UNIFY_BASE_URL). A missing backend is a test environment
# failure, not a reason to silently skip integration coverage.


def _orchestra_health_urls() -> list[str]:
    url = (
        os.environ.get("ORCHESTRA_URL")
        or os.environ.get("UNIFY_BASE_URL")
        or "http://127.0.0.1:8000/v0"
    )
    base = url.rstrip("/")
    candidates = [f"{base}/health"]
    if base.endswith("/v0"):
        candidates.append(f"{base[: -len('/v0')]}/health")
    else:
        candidates.append(f"{base}/v0/health")
    return list(dict.fromkeys(candidates))


def _orchestra_reachability_error() -> str | None:
    """Try known health endpoints. Return None if Orchestra is alive."""
    errors: list[str] = []
    try:
        import urllib.error
        import urllib.request

        for health_url in _orchestra_health_urls():
            req = urllib.request.Request(health_url, method="GET")
            try:
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if 200 <= resp.status < 300:
                        return None
                    errors.append(f"{health_url} returned HTTP {resp.status}")
            except urllib.error.HTTPError as exc:
                errors.append(f"{health_url} returned HTTP {exc.code}")
            except (
                urllib.error.URLError,
                ConnectionError,
                TimeoutError,
                OSError,
            ) as exc:
                errors.append(f"{health_url} failed: {exc}")
    except Exception as exc:
        errors.append(f"health check setup failed: {exc}")
    return "Orchestra is unreachable. Checked: " + "; ".join(errors)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "no_orchestra: test does not require a reachable Orchestra backend",
    )


def pytest_collection_modifyitems(config, items):
    """Fail orchestra-dependent test runs if the backend is unreachable."""
    error = _orchestra_reachability_error()
    if error is None:
        return

    if any("no_orchestra" not in item.keywords for item in items):
        raise pytest.UsageError(error)


# ---------------------------------------------------------------------------
# Coordinator organization provisioning
# ---------------------------------------------------------------------------
#
# The org/team/assistant-management SDK surface is org-scoped, but the seeded
# test user starts without an organization. These tests create a real one
# against the configured Orchestra and tear it down afterwards.


@dataclass(frozen=True)
class CoordinatorOrg:
    """A live organization provisioned for coordinator integration tests."""

    organization_id: int
    api_key: str


@pytest.fixture(scope="module")
def coordinator_org():
    """Provision an organization for the seeded user and clean it up.

    Organization creation returns an org-scoped API key used for every
    subsequent org-scoped call. Deleting the organization on teardown removes
    it and anything created under it.
    """
    import unify  # noqa: PLC0415
    from unify.utils import http  # noqa: PLC0415
    from unify.utils.helpers import _create_request_header  # noqa: PLC0415

    name = f"Coordinator SDK {uuid.uuid4().hex[:12]}"
    response = http.post(
        f"{unify.BASE_URL}/organizations",
        headers=_create_request_header(None),
        json={"name": name},
        timeout=30,
    )
    assert response.status_code == 201, response.text
    organization = response.json()

    try:
        yield CoordinatorOrg(
            organization_id=int(organization["id"]),
            api_key=organization["api_key"],
        )
    finally:
        http.delete(
            f"{unify.BASE_URL}/organizations/{organization['id']}",
            headers=_create_request_header(None),
            raise_for_status=False,
            timeout=30,
        )
