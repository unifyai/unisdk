"""Unify python module."""

import os
from typing import Optional, Union

if "ORCHESTRA_URL" in os.environ.keys():
    BASE_URL = os.environ["ORCHESTRA_URL"]
else:
    BASE_URL = "https://api.unify.ai/v0"


UNIFY_DIR = os.path.dirname(__file__)


# Platform API utilities
from .platform import deduct_credits, get_user_basic_info

# Contexts
from .contexts import (
    add_logs_to_context,
    commit_context,
    create_context,
    create_contexts,
    delete_context,
    get_context,
    get_context_commits,
    get_contexts,
    rename_context,
    rollback_context,
)

# Projects
from .projects import (
    commit_project,
    create_project,
    delete_project,
    delete_project_contexts,
    get_project_commits,
    list_projects,
    rollback_project,
)

# Logs
from .logs import (
    ACTIVE_LOG,
    CONTEXT_READ,
    CONTEXT_WRITE,
    Log,
    LogGroup,
    atomic_update,
    create_derived_logs,
    create_fields,
    create_logs,
    delete_fields,
    delete_logs,
    get_active_context,
    get_fields,
    get_groups,
    get_logs,
    get_logs_metric,
    join_logs,
    log,
    rename_field,
    set_context,
    set_user_logging,
    unset_context,
    update_logs,
)

# Async Logging
from ._async_logger import AsyncLoggerManager

# Utils
from .utils import helpers, map, storage
from .utils.storage import get_signed_url, download_object
from .utils import http
from .utils.http import RequestError

# Assistants
from .assistants import list_assistants

# Project #
# --------#

PROJECT: Optional[str] = None


# noinspection PyShadowingNames
def activate(
    project: str,
    overwrite: Union[bool, str] = False,
    api_key: str = None,
) -> None:
    if project not in list_projects(api_key=api_key):
        create_project(project, api_key=api_key)
    elif overwrite:
        create_project(project, api_key=api_key, overwrite=overwrite)
    global PROJECT
    PROJECT = project


def active_project() -> str:
    global PROJECT
    if PROJECT is None:
        return os.environ.get("UNIFY_PROJECT")
    return PROJECT
