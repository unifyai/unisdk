# Load .env BEFORE importing unify - BASE_URL is evaluated at import time
from pathlib import Path

from dotenv import load_dotenv

# Look for .env in repo root (parent of tests/)
# override=True ensures .env takes precedence over shell environment
_repo_root = Path(__file__).resolve().parent.parent
load_dotenv(_repo_root / ".env", override=True)

import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
