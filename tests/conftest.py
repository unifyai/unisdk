import os

import unify


def pytest_sessionstart(session):
    if os.environ.get("CI"):
        unify.delete_logs()
