# Load .env BEFORE importing unify - BASE_URL is evaluated at import time
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Look for .env in repo root (parent of tests/)
# override=True ensures .env takes precedence over shell environment
_repo_root = Path(__file__).resolve().parent.parent
load_dotenv(_repo_root / ".env", override=True)

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
# Orchestra reachability gate (external-mode CI support)
# ---------------------------------------------------------------------------
#
# The integration test suite assumes an Orchestra backend is reachable at
# ORCHESTRA_URL (or UNIFY_BASE_URL — both env vars are checked by the
# unify client). In CI:
#   - Internal mode: the unify-testing environment is populated with
#     CLONE_TOKEN/GCP_SERVICE_ACCOUNT_JSON/UNIFY_KEY, the workflow clones
#     orchestra + starts a local server, and ORCHESTRA_URL points at it.
#   - External mode (no env secrets, or external-fork PR): the workflow's
#     secrets-check gate skips the orchestra clone/startup steps. The
#     tests then have no backend to talk to and would all fail with
#     ConnectionRefusedError or similar.
#
# Auto-skip orchestra-dependent tests when the backend isn't reachable, so
# external-mode CI runs the pure-unit tests (no-orchestra-required) and
# cleanly skips the rest. CI exits 0; the skipped-count tells the team
# that integration coverage is degraded for that run.
#
# A test is considered orchestra-dependent if it is NOT explicitly marked
# `no_orchestra` (the marker is opt-in for pure unit tests). This avoids
# having to mark ~200+ test functions individually.


def _orchestra_reachable() -> bool:
    """Try a quick HEAD/GET against ORCHESTRA_URL. Return True if alive."""
    url = (
        os.environ.get("ORCHESTRA_URL")
        or os.environ.get("UNIFY_BASE_URL")
        or "http://127.0.0.1:8000/v0"
    )
    # Strip trailing /v0 if present so we hit a known light endpoint
    base = url.rstrip("/")
    if base.endswith("/v0"):
        base = base[: -len("/v0")]
    health_url = f"{base}/health"
    try:
        import urllib.error
        import urllib.request

        req = urllib.request.Request(health_url, method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status < 500
    except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
        return False
    except Exception:
        return False


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "no_orchestra: test does not require a reachable Orchestra backend",
    )


def pytest_collection_modifyitems(config, items):
    """Skip orchestra-dependent tests if the backend is unreachable.

    External-mode CI (no CLONE_TOKEN → no local orchestra) falls through
    here so that the workflow exits cleanly without requiring per-test
    skip markers. When the unify-testing environment is later populated,
    internal-mode CI starts a local orchestra and this gate becomes a
    no-op (reachable → no skips applied).
    """
    if _orchestra_reachable():
        return

    skip_orchestra = pytest.mark.skip(
        reason=(
            "Orchestra unreachable (external/degraded CI mode). "
            "Populate the unify-testing environment secrets to enable "
            "internal-mode integration tests."
        ),
    )
    for item in items:
        if "no_orchestra" in item.keywords:
            continue
        item.add_marker(skip_orchestra)
