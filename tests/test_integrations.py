"""Tests for provider-backed integration runtime SDK helpers."""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock, patch

import unisdk
from unisdk import integrations


def _response(payload):
    response = MagicMock()
    response.json.return_value = payload
    return response


def test_list_integration_connections_uses_env_base_url_and_key_by_default(
    monkeypatch,
) -> None:
    monkeypatch.setenv("UNIFY_KEY", "env-key")
    monkeypatch.setattr(integrations, "BASE_URL", "http://orchestra.env/v0")
    with patch.object(
        integrations.http,
        "get",
        return_value=_response([{"connection_id": "conn-1"}]),
    ) as mock_get:
        result = unisdk.list_integration_connections(owner_scope="assistant")

    assert result == [{"connection_id": "conn-1"}]
    assert mock_get.call_args.args[0] == (
        "http://orchestra.env/v0/integrations/connections"
    )
    assert mock_get.call_args.kwargs["headers"]["Authorization"] == "Bearer env-key"


def test_list_integration_connections_preserves_owner_scope_params() -> None:
    with patch.object(
        integrations.http,
        "get",
        return_value=_response([{"connection_id": "conn-1"}]),
    ) as mock_get:
        result = unisdk.list_integration_connections(
            owner_scope="org",
            org_id=7,
            team_id=8,
            user_id="user-1",
            assistant_id=42,
            api_key="test-key",
        )

    assert result == [{"connection_id": "conn-1"}]
    assert mock_get.call_args.args[0] == (
        f"{integrations.BASE_URL}/integrations/connections"
    )
    assert mock_get.call_args.kwargs["params"] == {
        "owner_scope": "org",
        "org_id": 7,
        "team_id": 8,
        "user_id": "user-1",
        "assistant_id": 42,
    }


def test_run_integration_tool_posts_arguments_and_confirmation_context() -> None:
    with patch.object(
        integrations.http,
        "post",
        return_value=_response({"status": "ok"}),
    ) as mock_post:
        result = unisdk.run_integration_tool(
            "tool-1",
            {"query": "alice"},
            owner_scope="assistant",
            assistant_id=42,
            user_id="user-1",
            connection_id="conn-1",
            conversation_id="conversation-1",
            confirmation_token="confirm-1",
            approval_audit_id=17,
            backend_id="composio",
            provider_app_id="hubspot",
            canonical_app_slug="hubspot",
            app_display_name="HubSpot",
            provider_tool_id="hubspot.search_contacts",
            canonical_name="primitives.integrations.hubspot.search_contacts",
            function_manager_name="primitives_integrations__hubspot__search_contacts",
            tool_display_name="Search contacts",
            action_class="read",
            behavior_hints=["read_only"],
            required_scopes=["crm.objects.contacts.read"],
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            examples=[{"arguments": {"query": "alice"}}],
            confirmation_required=False,
            api_key="test-key",
        )

    assert result == {"status": "ok"}
    assert mock_post.call_args.args[0] == (
        f"{integrations.BASE_URL}/integrations/tools/tool-1/run"
    )
    assert mock_post.call_args.kwargs["json"] == {
        "arguments": {"query": "alice"},
        "owner_scope": "assistant",
        "user_id": "user-1",
        "assistant_id": 42,
        "connection_id": "conn-1",
        "conversation_id": "conversation-1",
        "confirmation_token": "confirm-1",
        "approval_audit_id": 17,
        "backend_id": "composio",
        "provider_app_id": "hubspot",
        "canonical_app_slug": "hubspot",
        "app_display_name": "HubSpot",
        "provider_tool_id": "hubspot.search_contacts",
        "canonical_name": "primitives.integrations.hubspot.search_contacts",
        "function_manager_name": "primitives_integrations__hubspot__search_contacts",
        "tool_display_name": "Search contacts",
        "action_class": "read",
        "behavior_hints": ["read_only"],
        "required_scopes": ["crm.objects.contacts.read"],
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "examples": [{"arguments": {"query": "alice"}}],
        "confirmation_required": False,
    }


def test_get_integration_tool_policy_uses_owner_params() -> None:
    with patch.object(
        integrations.http,
        "get",
        return_value=_response({"connection_id": "conn-1", "policies": []}),
    ) as mock_get:
        result = unisdk.get_integration_tool_policy(
            "conn-1",
            owner_scope="assistant",
            assistant_id=42,
            api_key="test-key",
        )

    assert result == {"connection_id": "conn-1", "policies": []}
    assert mock_get.call_args.args[0] == (
        f"{integrations.BASE_URL}/integrations/connections/conn-1/tool-policy"
    )
    assert mock_get.call_args.kwargs["params"] == {
        "owner_scope": "assistant",
        "assistant_id": 42,
    }


def test_patch_integration_tool_policy_sends_partial_policy_and_owner_params() -> None:
    with patch.object(
        integrations.http,
        "patch",
        return_value=_response({"connection_id": "conn-1", "policies": []}),
    ) as mock_patch:
        result = unisdk.patch_integration_tool_policy(
            "conn-1",
            tool_policies={"tool-1": "auto"},
            bulk_approval_level="specific_approval",
            action_classes=["write"],
            owner_scope="assistant",
            assistant_id=42,
            api_key="test-key",
        )

    assert result == {"connection_id": "conn-1", "policies": []}
    assert mock_patch.call_args.args[0] == (
        f"{integrations.BASE_URL}/integrations/connections/conn-1/tool-policy"
    )
    assert mock_patch.call_args.kwargs["params"] == {
        "owner_scope": "assistant",
        "assistant_id": 42,
    }
    assert mock_patch.call_args.kwargs["json"] == {
        "tool_policies": {"tool-1": "auto"},
        "bulk_approval_level": "specific_approval",
        "action_classes": ["write"],
        "reset_to_defaults": False,
    }


def test_approve_integration_tool_execution_posts_owner_context() -> None:
    with patch.object(
        integrations.http,
        "post",
        return_value=_response(
            {"status": "approved", "confirmation_token": "confirm-1"},
        ),
    ) as mock_post:
        result = unisdk.approve_integration_tool_execution(
            17,
            scope="tool",
            persist_policy=True,
            approval_level="auto",
            actor_id="actor-1",
            owner_scope="assistant",
            assistant_id=42,
            api_key="test-key",
        )

    assert result == {"status": "approved", "confirmation_token": "confirm-1"}
    assert mock_post.call_args.args[0] == (
        f"{integrations.BASE_URL}/integrations/tool-executions/17/approve"
    )
    assert mock_post.call_args.kwargs["json"] == {
        "scope": "tool",
        "persist_policy": True,
        "approval_level": "auto",
        "actor_id": "actor-1",
        "owner_scope": "assistant",
        "assistant_id": 42,
    }


def test_deny_integration_tool_execution_posts_owner_context() -> None:
    with patch.object(
        integrations.http,
        "post",
        return_value=_response({"status": "denied"}),
    ) as mock_post:
        result = unisdk.deny_integration_tool_execution(
            17,
            scope="once",
            persist_policy=False,
            actor_id="actor-1",
            reason="not needed",
            owner_scope="assistant",
            assistant_id=42,
            api_key="test-key",
        )

    assert result == {"status": "denied"}
    assert mock_post.call_args.args[0] == (
        f"{integrations.BASE_URL}/integrations/tool-executions/17/deny"
    )
    assert mock_post.call_args.kwargs["json"] == {
        "scope": "once",
        "persist_policy": False,
        "approval_level": "forbidden",
        "actor_id": "actor-1",
        "reason": "not needed",
        "owner_scope": "assistant",
        "assistant_id": 42,
    }


def test_test_integration_connection_posts_health_check_endpoint() -> None:
    with patch.object(
        integrations.http,
        "post",
        return_value=_response({"connection_id": "conn-1", "health": "ok"}),
    ) as mock_post:
        result = unisdk.test_integration_connection(
            "conn-1",
            api_key="test-key",
            base_url="http://orchestra.local/v0/",
        )

    assert result == {"connection_id": "conn-1", "health": "ok"}
    assert mock_post.call_args.args[0] == (
        "http://orchestra.local/v0/integrations/connections/conn-1/test"
    )
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer test-key"


def test_upsert_integration_backend_posts_admin_backend_payload() -> None:
    with patch.object(
        integrations.http,
        "post",
        return_value=_response({"backend_id": "pipedream", "status": "enabled"}),
    ) as mock_post:
        result = unisdk.upsert_integration_backend(
            backend_id="pipedream",
            kind="pipedream",
            display_name="Pipedream",
            environment="prod",
            status="enabled",
            config_json={"timeout_seconds": 30},
            api_key="admin-key",
        )

    assert result == {"backend_id": "pipedream", "status": "enabled"}
    assert mock_post.call_args.args[0] == (
        f"{integrations.BASE_URL}/admin/integrations/backends"
    )
    assert mock_post.call_args.kwargs["json"] == {
        "backend_id": "pipedream",
        "kind": "pipedream",
        "environment": "prod",
        "display_name": "Pipedream",
        "status": "enabled",
        "credentials_secret_ref": None,
        "webhook_secret_ref": None,
        "allowed_orgs_or_tenants": [],
        "default_priority": 100,
        "config_json": {"timeout_seconds": 30},
    }
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer admin-key"


def test_patch_integration_backend_patches_admin_backend_payload() -> None:
    with patch.object(
        integrations.http,
        "patch",
        return_value=_response({"backend_id": "composio", "status": "disabled"}),
    ) as mock_patch:
        result = unisdk.patch_integration_backend(
            "composio",
            status="disabled",
            config_json={"priority": 50},
            api_key="admin-key",
            base_url="http://orchestra.local",
        )

    assert result == {"backend_id": "composio", "status": "disabled"}
    assert mock_patch.call_args.args[0] == (
        "http://orchestra.local/v0/admin/integrations/backends/composio"
    )
    assert mock_patch.call_args.kwargs["json"] == {
        "status": "disabled",
        "config_json": {"priority": 50},
    }
    assert mock_patch.call_args.kwargs["headers"]["Authorization"] == "Bearer admin-key"


def test_integration_helpers_do_not_import_provider_sdks() -> None:
    source = inspect.getsource(integrations).lower()

    assert "from composio" not in source
    assert "from pipedream" not in source
    assert "import composio" not in source
    assert "import pipedream" not in source


def test_unify_exports_runtime_integration_helpers_only() -> None:
    for name in [
        "get_integration_apps",
        "search_integration_apps",
        "get_integration_tools",
        "search_integration_tools",
        "get_integration_tool_schema",
        "sync_integrations",
    ]:
        assert not hasattr(unify, name)
    for name in [
        "list_integration_connections",
        "run_integration_tool",
        "get_integration_tool_policy",
        "patch_integration_backend",
    ]:
        assert hasattr(unify, name)
