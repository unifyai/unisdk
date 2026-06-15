"""Unify python module."""

import os
from typing import Optional, Union

if "ORCHESTRA_URL" in os.environ.keys():
    BASE_URL = os.environ["ORCHESTRA_URL"]
else:
    BASE_URL = "https://api.unify.ai/v0"


UNIFY_DIR = os.path.dirname(__file__)

__all__ = [
    # Configuration
    "BASE_URL",
    "UNIFY_DIR",
    "PROJECT",
    "activate",
    "active_project",
    # Platform
    "deduct_credits",
    "get_user_basic_info",
    # Contexts
    "add_logs_to_context",
    "commit_context",
    "create_context",
    "create_contexts",
    "delete_context",
    "get_context",
    "get_context_commits",
    "get_contexts",
    "rename_context",
    "rollback_context",
    # Projects
    "commit_project",
    "create_project",
    "delete_project",
    "delete_project_contexts",
    "get_project_commits",
    "list_projects",
    "rollback_project",
    # Logs
    "ACTIVE_LOG",
    "CONTEXT_READ",
    "CONTEXT_WRITE",
    "Log",
    "LogGroup",
    "atomic_update",
    "create_derived_logs",
    "create_fields",
    "create_logs",
    "delete_fields",
    "delete_logs",
    "get_active_context",
    "get_fields",
    "get_groups",
    "get_logs",
    "get_logs_metric",
    "join_logs",
    "join_query",
    "log",
    "rename_field",
    "set_context",
    "set_user_logging",
    "unset_context",
    "update_logs",
    # Async
    "AsyncLoggerManager",
    "AsyncSpendClient",
    "SpendRequestError",
    # Storage
    "get_signed_url",
    "download_object",
    # Assistants
    "create_assistant",
    "delegate_to_colleague",
    "delete_assistant",
    "list_assistants",
    "update_assistant_config",
    # Integrations
    "approve_integration_tool_execution",
    "deny_integration_tool_execution",
    "get_integration_tool_policy",
    "list_integration_connections",
    "patch_integration_backend",
    "patch_integration_tool_policy",
    "run_integration_tool",
    "test_integration_connection",
    "upsert_integration_backend",
    # Organizations
    "invite_org_member",
    "list_organizations",
    "list_org_members",
    # Teams
    "add_team_member",
    "create_team",
    "delete_team",
    "list_team_members",
    "list_teams",
    "list_teams_for_assistant",
    "remove_team_member",
    "update_team",
    # Errors
    "RequestError",
    # Submodules
    "agent",
    "helpers",
    "http",
    "map",
    "storage",
]

# Agent
from . import agent

# Async Logging
from ._async_logger import AsyncLoggerManager

# Assistants
from .assistants import (
    create_assistant,
    delegate_to_colleague,
    delete_assistant,
    list_assistants,
    update_assistant_config,
)

# Async Spend
from .async_admin import AsyncSpendClient, SpendRequestError

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

# Integrations
from .integrations import (
    approve_integration_tool_execution,
    deny_integration_tool_execution,
    get_integration_tool_policy,
    list_integration_connections,
    patch_integration_backend,
    patch_integration_tool_policy,
    run_integration_tool,
    test_integration_connection,
    upsert_integration_backend,
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
    join_query,
    log,
    rename_field,
    set_context,
    set_user_logging,
    unset_context,
    update_logs,
)

# Organizations
from .organizations import invite_org_member, list_org_members, list_organizations

# Platform API utilities
from .platform import deduct_credits, get_user_basic_info

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

# Teams
from .teams import (
    add_team_member,
    create_team,
    delete_team,
    list_team_members,
    list_teams,
    list_teams_for_assistant,
    remove_team_member,
    update_team,
)

# Utils
from .utils import helpers, http, map, storage
from .utils.storage import download_object, get_signed_url

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


def __getattr__(name: str):
    if name == "RequestError":
        return http.RequestError
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
