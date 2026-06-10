"""Tests for provider-backed integration SDK helpers."""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock, patch

import unify
from unify import integrations


def _response(payload):
    response = MagicMock()
    response.json.return_value = payload
    return response


def test_search_integration_apps_uses_env_api_key_by_default(monkeypatch) -> None:
    monkeypatch.setenv("UNIFY_KEY", "env-key")
    with patch.object(
        integrations.http,
        "post",
        return_value=_response([{"canonical_app_slug": "slack"}]),
    ) as mock_post:
        result = unify.search_integration_apps(
            "team chat",
            owner_scope="assistant",
            assistant_id=42,
        )

    assert result == [{"canonical_app_slug": "slack"}]
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer env-key"


def test_get_integration_tools_uses_env_api_key_by_default(monkeypatch) -> None:
    monkeypatch.setenv("UNIFY_KEY", "env-key")
    with patch.object(
        integrations.http,
        "post",
        return_value=_response({"items": [{"tool_id": "tool-1"}], "total": 1}),
    ) as mock_post:
        result = unify.get_integration_tools(
            owner_scope="assistant",
            assistant_id=42,
            canonical_app_slug="slack",
        )

    assert result["items"] == [{"tool_id": "tool-1"}]
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer env-key"


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
        result = unify.list_integration_connections(owner_scope="assistant")

    assert result == [{"connection_id": "conn-1"}]
    assert mock_get.call_args.args[0] == (
        "http://orchestra.env/v0/integrations/connections"
    )
    assert mock_get.call_args.kwargs["headers"]["Authorization"] == "Bearer env-key"


def test_get_integration_apps_posts_get_payload_with_pagination_and_base_url() -> None:
    with patch.object(
        integrations.http,
        "post",
        return_value=_response(
            {
                "items": [{"canonical_app_slug": "hubspot"}],
                "total": 1,
                "limit": 5,
                "offset": 0,
            },
        ),
    ) as mock_post:
        result = unify.get_integration_apps(
            query="crm",
            source_type="native",
            owner_scope="assistant",
            assistant_id=42,
            user_id="user-1",
            limit=5,
            offset=0,
            api_key="test-key",
            base_url="http://orchestra.local",
        )

    assert result["items"] == [{"canonical_app_slug": "hubspot"}]
    mock_post.assert_called_once()
    url = mock_post.call_args.args[0]
    kwargs = mock_post.call_args.kwargs
    assert url == "http://orchestra.local/v0/integrations/apps/get"
    assert kwargs["json"] == {
        "query": "crm",
        "source_type": "native",
        "owner_scope": "assistant",
        "user_id": "user-1",
        "assistant_id": 42,
        "limit": 5,
        "offset": 0,
    }
    assert kwargs["headers"]["Authorization"] == "Bearer test-key"


def test_list_integration_apps_is_backward_compatible_alias() -> None:
    with patch.object(
        integrations.http,
        "post",
        return_value=_response(
            {
                "items": [{"canonical_app_slug": "hubspot"}],
                "total": 1,
                "limit": 100,
                "offset": 0,
            },
        ),
    ) as mock_post:
        result = unify.list_integration_apps(
            query="crm",
            source_type="third_party",
            owner_scope="assistant",
            assistant_id=42,
            api_key="test-key",
            base_url="http://orchestra.local/v0",
        )

    assert result == [{"canonical_app_slug": "hubspot"}]
    assert (
        mock_post.call_args.args[0] == "http://orchestra.local/v0/integrations/apps/get"
    )
    assert mock_post.call_args.kwargs["json"]["source_type"] == "third_party"


def test_search_integration_apps_posts_search_payload() -> None:
    with patch.object(
        integrations.http,
        "post",
        return_value=_response([{"canonical_app_slug": "slack", "score": 0.91}]),
    ) as mock_post:
        result = unify.search_integration_apps(
            "team chat",
            source_type="native",
            owner_scope="assistant",
            assistant_id=42,
            user_id="user-1",
            limit=7,
            offset=2,
            api_key="test-key",
        )

    assert result == [{"canonical_app_slug": "slack", "score": 0.91}]
    assert mock_post.call_args.args[0] == (
        f"{integrations.BASE_URL}/integrations/apps/search"
    )
    assert mock_post.call_args.kwargs["json"] == {
        "query": "team chat",
        "source_type": "native",
        "owner_scope": "assistant",
        "user_id": "user-1",
        "assistant_id": 42,
        "limit": 7,
        "offset": 2,
    }


def test_list_integration_connections_preserves_owner_scope_params() -> None:
    with patch.object(
        integrations.http,
        "get",
        return_value=_response([{"connection_id": "conn-1"}]),
    ) as mock_get:
        result = unify.list_integration_connections(
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


def test_search_integration_tools_posts_query_scope_and_limit() -> None:
    with patch.object(
        integrations.http,
        "post",
        return_value=_response([{"tool_id": "composio:hubspot:search_contacts"}]),
    ) as mock_post:
        result = unify.search_integration_tools(
            "HubSpot leads",
            owner_scope="assistant",
            assistant_id=42,
            user_id="user-1",
            canonical_app_slug="hubspot",
            include_unconnected=False,
            limit=5,
            offset=3,
            api_key="test-key",
        )

    assert result == [{"tool_id": "composio:hubspot:search_contacts"}]
    assert mock_post.call_args.args[0] == (
        f"{integrations.BASE_URL}/integrations/tools/search"
    )
    assert mock_post.call_args.kwargs["json"] == {
        "query": "HubSpot leads",
        "owner_scope": "assistant",
        "user_id": "user-1",
        "assistant_id": 42,
        "canonical_app_slug": "hubspot",
        "include_unconnected": False,
        "limit": 5,
        "offset": 3,
    }
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer test-key"


def test_get_integration_tools_posts_filter_payload_with_total_pagination() -> None:
    with patch.object(
        integrations.http,
        "post",
        return_value=_response(
            {
                "items": [{"tool_id": "composio:hubspot:search_contacts"}],
                "total": 12,
                "limit": 2,
                "offset": 4,
            },
        ),
    ) as mock_post:
        result = unify.get_integration_tools(
            owner_scope="assistant",
            assistant_id=42,
            user_id="user-1",
            canonical_app_slug="hubspot",
            activation_state="connected_ready",
            include_unconnected=False,
            limit=2,
            offset=4,
            api_key="test-key",
        )

    assert result["total"] == 12
    assert mock_post.call_args.args[0] == (
        f"{integrations.BASE_URL}/integrations/tools/get"
    )
    assert mock_post.call_args.kwargs["json"] == {
        "owner_scope": "assistant",
        "user_id": "user-1",
        "assistant_id": 42,
        "canonical_app_slug": "hubspot",
        "activation_state": "connected_ready",
        "include_unconnected": False,
        "limit": 2,
        "offset": 4,
    }


def test_get_integration_tool_schema_calls_schema_endpoint_with_scope() -> None:
    with patch.object(
        integrations.http,
        "get",
        return_value=_response({"tool_id": "tool-1", "input_schema": {}}),
    ) as mock_get:
        result = unify.get_integration_tool_schema(
            "tool-1",
            owner_scope="assistant",
            assistant_id=42,
            user_id="user-1",
            api_key="test-key",
        )

    assert result == {"tool_id": "tool-1", "input_schema": {}}
    assert mock_get.call_args.args[0] == (
        f"{integrations.BASE_URL}/integrations/tools/tool-1/schema"
    )
    assert mock_get.call_args.kwargs["params"] == {
        "owner_scope": "assistant",
        "user_id": "user-1",
        "assistant_id": 42,
    }


def test_run_integration_tool_posts_arguments_and_confirmation_context() -> None:
    with patch.object(
        integrations.http,
        "post",
        return_value=_response({"status": "ok"}),
    ) as mock_post:
        result = unify.run_integration_tool(
            "tool-1",
            {"query": "alice"},
            owner_scope="assistant",
            assistant_id=42,
            user_id="user-1",
            connection_id="conn-1",
            conversation_id="conversation-1",
            confirmation_token="confirm-1",
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
    }


def test_test_integration_connection_posts_health_check_endpoint() -> None:
    with patch.object(
        integrations.http,
        "post",
        return_value=_response({"connection_id": "conn-1", "health": "ok"}),
    ) as mock_post:
        result = unify.test_integration_connection(
            "conn-1",
            api_key="test-key",
            base_url="http://orchestra.local/v0/",
        )

    assert result == {"connection_id": "conn-1", "health": "ok"}
    assert mock_post.call_args.args[0] == (
        "http://orchestra.local/v0/integrations/connections/conn-1/test"
    )
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer test-key"


def test_sync_integrations_posts_admin_catalog_payload() -> None:
    app = {
        "provider_app_id": "linear",
        "canonical_app_slug": "linear",
        "display_name": "Linear",
    }
    tool = {
        "provider_app_id": "linear",
        "canonical_app_slug": "linear",
        "provider_tool_id": "linear-list-issues",
        "name": "list_issues",
        "display_name": "List issues",
        "description": "List issues.",
    }
    with patch.object(
        integrations.http,
        "post",
        return_value=_response({"apps_upserted": 1, "tools_upserted": 1}),
    ) as mock_post:
        result = unify.sync_integrations(
            backend_id="provider-backend",
            apps=[app],
            tools=[tool],
            cache_version="sync-v2",
            api_key="admin-key",
        )

    assert result == {"apps_upserted": 1, "tools_upserted": 1}
    assert mock_post.call_args.args[0] == (
        f"{integrations.BASE_URL}/admin/integrations/sync"
    )
    assert mock_post.call_args.kwargs["json"] == {
        "backend_id": "provider-backend",
        "cache_version": "sync-v2",
        "source_type": "third_party",
        "apps": [app],
        "tools": [tool],
        "app_slugs": [],
        "tool_limit_per_app": 0,
        "component_limit_per_app": 0,
        "include_all_managed_apps": False,
        "include_all_apps": False,
        "create_auth_configs": True,
    }
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer admin-key"


def test_sync_integrations_posts_app_only_native_payload() -> None:
    app = {"provider_app_id": "github", "canonical_app_slug": "github"}
    with patch.object(
        integrations.http,
        "post",
        return_value=_response({"apps_upserted": 1, "tools_upserted": 0}),
    ) as mock_post:
        result = unify.sync_integrations(
            backend_id="unity_native",
            source_type="native",
            cache_version="unity-deploy-native-v1",
            apps=[app],
            api_key="admin-key",
        )

    assert result == {"apps_upserted": 1, "tools_upserted": 0}
    assert mock_post.call_args.kwargs["json"] == {
        "backend_id": "unity_native",
        "cache_version": "unity-deploy-native-v1",
        "source_type": "native",
        "apps": [app],
        "tools": [],
        "app_slugs": [],
        "tool_limit_per_app": 0,
        "component_limit_per_app": 0,
        "include_all_managed_apps": False,
        "include_all_apps": False,
        "create_auth_configs": True,
    }


def test_sync_integrations_posts_composio_live_sync_payload() -> None:
    with patch.object(
        integrations.http,
        "post",
        return_value=_response({"apps_upserted": 20, "tools_upserted": 40}),
    ) as mock_post:
        result = unify.sync_integrations(
            backend_id="composio",
            app_slugs=["DISCORD", "GOOGLEDRIVE"],
            tool_limit_per_app=10,
            include_all_managed_apps=False,
            create_auth_configs=True,
            cache_version="local-composio-first-wave",
            api_key="admin-key",
        )

    assert result == {"apps_upserted": 20, "tools_upserted": 40}
    assert mock_post.call_args.args[0] == (
        f"{integrations.BASE_URL}/admin/integrations/sync"
    )
    assert mock_post.call_args.kwargs["json"] == {
        "backend_id": "composio",
        "source_type": "third_party",
        "apps": [],
        "tools": [],
        "app_slugs": ["DISCORD", "GOOGLEDRIVE"],
        "tool_limit_per_app": 10,
        "component_limit_per_app": 0,
        "include_all_managed_apps": False,
        "include_all_apps": False,
        "create_auth_configs": True,
        "cache_version": "local-composio-first-wave",
    }
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer admin-key"


def test_upsert_integration_backend_posts_admin_backend_payload() -> None:
    with patch.object(
        integrations.http,
        "post",
        return_value=_response({"backend_id": "pipedream", "status": "enabled"}),
    ) as mock_post:
        result = unify.upsert_integration_backend(
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
        result = unify.patch_integration_backend(
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


def test_unify_exports_integration_helpers() -> None:
    for name in [
        "get_integration_apps",
        "search_integration_apps",
        "sync_integrations",
        "patch_integration_backend",
    ]:
        assert hasattr(unify, name)
