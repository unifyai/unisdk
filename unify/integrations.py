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


def get_integration_apps(
    *,
    owner_scope: str = "assistant",
    org_id: Optional[int] = None,
    team_id: Optional[int] = None,
    user_id: Optional[str] = None,
    assistant_id: Optional[int] = None,
    query: Optional[str] = None,
    source_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Get provider-backed integration apps with direct filters and pagination."""

    headers = _create_request_header(api_key)
    params = _clean_payload(
        {
            "owner_scope": owner_scope,
            "org_id": org_id,
            "team_id": team_id,
            "user_id": user_id,
            "assistant_id": assistant_id,
            "query": query,
            "source_type": source_type,
            "limit": limit,
            "offset": offset,
        },
    )
    return http.get(
        f"{_api_base_url(base_url)}/integrations/apps",
        headers=headers,
        params=params,
    ).json()


def list_integration_apps(
    *,
    query: Optional[str] = None,
    source_type: Optional[str] = None,
    owner_scope: str = "assistant",
    org_id: Optional[int] = None,
    team_id: Optional[int] = None,
    user_id: Optional[str] = None,
    assistant_id: Optional[int] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Backward-compatible alias for ``get_integration_apps(...)[\"items\"]``."""

    response = get_integration_apps(
        query=query or None,
        source_type=source_type,
        owner_scope=owner_scope,
        org_id=org_id,
        team_id=team_id,
        user_id=user_id,
        assistant_id=assistant_id,
        api_key=api_key,
        base_url=base_url,
    )
    if isinstance(response, dict) and "items" in response:
        return response["items"]
    return response  # type: ignore[return-value]


def search_integration_apps(
    query: Optional[str] = None,
    *,
    source_type: Optional[str] = None,
    owner_scope: str = "assistant",
    org_id: Optional[int] = None,
    team_id: Optional[int] = None,
    user_id: Optional[str] = None,
    assistant_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search provider-backed integration apps through the global catalog index."""

    headers = _create_request_header(api_key)
    params = _clean_payload(
        {
            "query": query,
            "source_type": source_type,
            "owner_scope": owner_scope,
            "org_id": org_id,
            "team_id": team_id,
            "user_id": user_id,
            "assistant_id": assistant_id,
            "limit": limit,
            "offset": offset,
        },
    )
    return http.get(
        f"{_api_base_url(base_url)}/integrations/apps/search",
        headers=headers,
        params=params,
    ).json()


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


def get_integration_tools(
    *,
    owner_scope: str = "assistant",
    org_id: Optional[int] = None,
    team_id: Optional[int] = None,
    user_id: Optional[str] = None,
    assistant_id: Optional[int] = None,
    canonical_app_slug: Optional[str] = None,
    activation_state: Optional[str] = None,
    include_unconnected: bool = False,
    limit: int = 100,
    offset: int = 0,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Get provider tools with direct filters and count-bearing pagination."""

    headers = _create_request_header(api_key)
    params = _clean_payload(
        {
            "owner_scope": owner_scope,
            "org_id": org_id,
            "team_id": team_id,
            "user_id": user_id,
            "assistant_id": assistant_id,
            "canonical_app_slug": canonical_app_slug,
            "activation_state": activation_state,
            "include_unconnected": include_unconnected,
            "limit": limit,
            "offset": offset,
        },
    )
    return http.get(
        f"{_api_base_url(base_url)}/integrations/tools",
        headers=headers,
        params=params,
    ).json()


def search_integration_tools(
    query: Optional[str] = None,
    *,
    owner_scope: str = "assistant",
    org_id: Optional[int] = None,
    team_id: Optional[int] = None,
    user_id: Optional[str] = None,
    assistant_id: Optional[int] = None,
    include_unconnected: bool = True,
    canonical_app_slug: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search provider tools through the global catalog index."""

    headers = _create_request_header(api_key)
    params = _clean_payload(
        {
            "query": query,
            "owner_scope": owner_scope,
            "org_id": org_id,
            "team_id": team_id,
            "user_id": user_id,
            "assistant_id": assistant_id,
            "canonical_app_slug": canonical_app_slug,
            "include_unconnected": include_unconnected,
            "limit": limit,
            "offset": offset,
        },
    )
    return http.get(
        f"{_api_base_url(base_url)}/integrations/tools/search",
        headers=headers,
        params=params,
    ).json()


def get_integration_tool_schema(
    tool_id: str,
    *,
    owner_scope: str = "assistant",
    org_id: Optional[int] = None,
    team_id: Optional[int] = None,
    user_id: Optional[str] = None,
    assistant_id: Optional[int] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Get JSON schema, examples, and activation state for a provider tool."""

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
        f"{_api_base_url(base_url)}/integrations/tools/{tool_id}/schema",
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
        },
    )
    return http.post(
        f"{_api_base_url(base_url)}/integrations/tools/{tool_id}/run",
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


def sync_integrations(
    *,
    backend_id: str,
    apps: Optional[List[Dict[str, Any]]] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    cache_version: str = "provider-sync-v1",
    source_type: str = "third_party",
    app_slugs: Optional[List[str]] = None,
    tool_limit_per_app: int = 0,
    component_limit_per_app: int = 0,
    include_all_managed_apps: bool = False,
    include_all_apps: bool = False,
    create_auth_configs: bool = True,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Sync native and provider-backed integrations through one admin API.

    ``backend_id`` selects the backend. Native/custom catalog publishers pass
    normalized ``apps``/``tools``. Live provider syncs for backends such as
    Composio and Pipedream pass bounded provider options like ``app_slugs`` and
    per-app limits; Orchestra handles provider-specific dispatch internally.
    """

    headers = _create_request_header(api_key)
    body = {
        "backend_id": backend_id,
        "cache_version": cache_version,
        "source_type": source_type,
        "apps": apps or [],
        "tools": tools or [],
        "app_slugs": app_slugs or [],
        "tool_limit_per_app": tool_limit_per_app,
        "component_limit_per_app": component_limit_per_app,
        "include_all_managed_apps": include_all_managed_apps,
        "include_all_apps": include_all_apps,
        "create_auth_configs": create_auth_configs,
    }
    return http.post(
        f"{_api_base_url(base_url)}/admin/integrations/sync",
        headers=headers,
        json=body,
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
