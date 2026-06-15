"""Thin SDK helpers for provider-backed integration APIs."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from unify import BASE_URL
from unify.utils import http
from unify.utils.helpers import _create_request_header


def _api_base_url(base_url: Optional[str] = None) -> str:
    """Return a normalized Orchestra v0 base URL."""

    normalized = (base_url or BASE_URL).rstrip("/")
    if normalized.endswith("/v0"):
        return normalized
    return f"{normalized}/v0"


def _clean_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def list_integration_connections(
    *,
    owner_scope: str = "assistant",
    org_id: Optional[int] = None,
    team_id: Optional[int] = None,
    user_id: Optional[str] = None,
    assistant_id: Optional[int] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List provider-backed integration connections for an owner scope."""

    headers = _create_request_header(api_key)
    params = _clean_payload(
        {
            "owner_scope": owner_scope,
            "org_id": org_id,
            "team_id": team_id,
            "user_id": user_id,
            "assistant_id": assistant_id,
        },
    )
    return http.get(
        f"{_api_base_url(base_url)}/integrations/connections",
        headers=headers,
        params=params,
    ).json()


def run_integration_tool(
    tool_id: str,
    arguments: Optional[Dict[str, Any]] = None,
    *,
    owner_scope: str = "assistant",
    org_id: Optional[int] = None,
    team_id: Optional[int] = None,
    user_id: Optional[str] = None,
    assistant_id: Optional[int] = None,
    connection_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    confirmation_token: Optional[str] = None,
    approval_audit_id: Optional[int] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute a provider tool through Orchestra policy and audit checks."""

    headers = _create_request_header(api_key)
    body = _clean_payload(
        {
            "arguments": arguments or {},
            "owner_scope": owner_scope,
            "org_id": org_id,
            "team_id": team_id,
            "user_id": user_id,
            "assistant_id": assistant_id,
            "connection_id": connection_id,
            "conversation_id": conversation_id,
            "confirmation_token": confirmation_token,
            "approval_audit_id": approval_audit_id,
        },
    )
    return http.post(
        f"{_api_base_url(base_url)}/integrations/tools/{tool_id}/run",
        headers=headers,
        json=body,
    ).json()


def get_integration_tool_policy(
    connection_id: str,
    *,
    owner_scope: str = "assistant",
    org_id: Optional[int] = None,
    team_id: Optional[int] = None,
    user_id: Optional[str] = None,
    assistant_id: Optional[int] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Get durable tool policy for one provider integration connection."""

    headers = _create_request_header(api_key)
    params = _clean_payload(
        {
            "owner_scope": owner_scope,
            "org_id": org_id,
            "team_id": team_id,
            "user_id": user_id,
            "assistant_id": assistant_id,
        },
    )
    return http.get(
        f"{_api_base_url(base_url)}/integrations/connections/{connection_id}/tool-policy",
        headers=headers,
        params=params,
    ).json()


def patch_integration_tool_policy(
    connection_id: str,
    *,
    tool_policies: Optional[Dict[str, str]] = None,
    bulk_approval_level: Optional[str] = None,
    action_classes: Optional[List[str]] = None,
    reset_to_defaults: bool = False,
    owner_scope: str = "assistant",
    org_id: Optional[int] = None,
    team_id: Optional[int] = None,
    user_id: Optional[str] = None,
    assistant_id: Optional[int] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Patch durable tool policy for one provider integration connection."""

    headers = _create_request_header(api_key)
    params = _clean_payload(
        {
            "owner_scope": owner_scope,
            "org_id": org_id,
            "team_id": team_id,
            "user_id": user_id,
            "assistant_id": assistant_id,
        },
    )
    body = _clean_payload(
        {
            "tool_policies": tool_policies or {},
            "bulk_approval_level": bulk_approval_level,
            "action_classes": action_classes,
            "reset_to_defaults": reset_to_defaults,
        },
    )
    return http.patch(
        f"{_api_base_url(base_url)}/integrations/connections/{connection_id}/tool-policy",
        headers=headers,
        params=params,
        json=body,
    ).json()


def approve_integration_tool_execution(
    audit_id: int,
    *,
    scope: str = "once",
    persist_policy: bool = False,
    approval_level: str = "auto",
    actor_id: Optional[str] = None,
    expires_at: Optional[str] = None,
    owner_scope: str = "assistant",
    org_id: Optional[int] = None,
    team_id: Optional[int] = None,
    user_id: Optional[str] = None,
    assistant_id: Optional[int] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Approve a pending provider tool execution audit."""

    headers = _create_request_header(api_key)
    body = _clean_payload(
        {
            "scope": scope,
            "persist_policy": persist_policy,
            "approval_level": approval_level,
            "actor_id": actor_id,
            "expires_at": expires_at,
            "owner_scope": owner_scope,
            "org_id": org_id,
            "team_id": team_id,
            "user_id": user_id,
            "assistant_id": assistant_id,
        },
    )
    return http.post(
        f"{_api_base_url(base_url)}/integrations/tool-executions/{audit_id}/approve",
        headers=headers,
        json=body,
    ).json()


def deny_integration_tool_execution(
    audit_id: int,
    *,
    scope: str = "once",
    persist_policy: bool = False,
    approval_level: str = "forbidden",
    actor_id: Optional[str] = None,
    reason: Optional[str] = None,
    owner_scope: str = "assistant",
    org_id: Optional[int] = None,
    team_id: Optional[int] = None,
    user_id: Optional[str] = None,
    assistant_id: Optional[int] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Deny a pending provider tool execution audit."""

    headers = _create_request_header(api_key)
    body = _clean_payload(
        {
            "scope": scope,
            "persist_policy": persist_policy,
            "approval_level": approval_level,
            "actor_id": actor_id,
            "reason": reason,
            "owner_scope": owner_scope,
            "org_id": org_id,
            "team_id": team_id,
            "user_id": user_id,
            "assistant_id": assistant_id,
        },
    )
    return http.post(
        f"{_api_base_url(base_url)}/integrations/tool-executions/{audit_id}/deny",
        headers=headers,
        json=body,
    ).json()


def test_integration_connection(
    connection_id: str,
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Run a provider connection health check through Orchestra."""

    headers = _create_request_header(api_key)
    return http.post(
        f"{_api_base_url(base_url)}/integrations/connections/{connection_id}/test",
        headers=headers,
    ).json()


def upsert_integration_backend(
    *,
    backend_id: str,
    kind: str,
    display_name: str,
    environment: str = "prod",
    status: str = "enabled",
    credentials_secret_ref: Optional[str] = None,
    webhook_secret_ref: Optional[str] = None,
    allowed_orgs_or_tenants: Optional[List[str]] = None,
    default_priority: int = 100,
    config_json: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Upsert a provider backend through Orchestra admin integration APIs."""

    headers = _create_request_header(api_key)
    body = {
        "backend_id": backend_id,
        "kind": kind,
        "environment": environment,
        "display_name": display_name,
        "status": status,
        "credentials_secret_ref": credentials_secret_ref,
        "webhook_secret_ref": webhook_secret_ref,
        "allowed_orgs_or_tenants": allowed_orgs_or_tenants or [],
        "default_priority": default_priority,
        "config_json": config_json or {},
    }
    return http.post(
        f"{_api_base_url(base_url)}/admin/integrations/backends",
        headers=headers,
        json=body,
    ).json()


def patch_integration_backend(
    backend_id: str,
    *,
    status: Optional[str] = None,
    credentials_secret_ref: Optional[str] = None,
    webhook_secret_ref: Optional[str] = None,
    allowed_orgs_or_tenants: Optional[List[str]] = None,
    default_priority: Optional[int] = None,
    config_json: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Patch backend enablement/config without resending the full backend row."""

    headers = _create_request_header(api_key)
    body = _clean_payload(
        {
            "status": status,
            "credentials_secret_ref": credentials_secret_ref,
            "webhook_secret_ref": webhook_secret_ref,
            "allowed_orgs_or_tenants": allowed_orgs_or_tenants,
            "default_priority": default_priority,
            "config_json": config_json,
        },
    )
    return http.patch(
        f"{_api_base_url(base_url)}/admin/integrations/backends/{backend_id}",
        headers=headers,
        json=body,
    ).json()
