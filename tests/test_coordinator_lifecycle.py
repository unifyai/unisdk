import inspect
import uuid
from typing import Iterator

import pytest
from tests.coordinator_helpers import (
    PreviewOrganization,
    managed_preview_organization,
)

import unify
from unify.utils import http


@pytest.fixture(scope="module")
def preview_org() -> Iterator[PreviewOrganization]:
    with managed_preview_organization() as organization:
        yield organization


def test_public_coordinator_sdk_exports() -> None:
    from unify import (  # noqa: PLC0415
        RequestError,
        add_team_member,
        create_assistant,
        create_team,
        delegate_to_colleague,
        delete_assistant,
        delete_team,
        invite_org_member,
        list_assistants,
        list_org_members,
        list_organizations,
        list_team_members,
        list_teams,
        list_teams_for_assistant,
        remove_team_member,
        update_assistant_config,
        update_team,
    )

    assert add_team_member is unify.add_team_member
    assert create_assistant is unify.create_assistant
    assert create_team is unify.create_team
    assert delegate_to_colleague is unify.delegate_to_colleague
    assert delete_assistant is unify.delete_assistant
    assert delete_team is unify.delete_team
    assert invite_org_member is unify.invite_org_member
    assert list_assistants is unify.list_assistants
    assert list_organizations is unify.list_organizations
    assert list_org_members is unify.list_org_members
    assert list_team_members is unify.list_team_members
    assert list_teams is unify.list_teams
    assert list_teams_for_assistant is unify.list_teams_for_assistant
    assert remove_team_member is unify.remove_team_member
    assert update_assistant_config is unify.update_assistant_config
    assert update_team is unify.update_team
    assert RequestError is http.RequestError

    list_signature = inspect.signature(unify.list_assistants)
    assert "list_all_org" in list_signature.parameters
    assert "organization_id" not in list_signature.parameters

    create_signature = inspect.signature(unify.create_assistant)
    assert "organization_id" not in create_signature.parameters
    assert "is_coordinator" not in create_signature.parameters

    team_signature = inspect.signature(unify.create_team)
    assert "organization_id" in team_signature.parameters
    assert "description" in team_signature.parameters

    delegate_signature = inspect.signature(unify.delegate_to_colleague)
    assert list(delegate_signature.parameters) == [
        "target_assistant_id",
        "instruction",
        "intent",
        "dedupe_key",
        "related_context",
        "api_key",
    ]


def test_invite_org_member_sdk_export() -> None:
    from unify import invite_org_member  # noqa: PLC0415

    assert invite_org_member is unify.invite_org_member
    assert callable(unify.invite_org_member)


def test_delegate_to_colleague_posts_delegate_payload(monkeypatch) -> None:
    captured = {}

    class _Response:
        def json(self):
            return {"info": {"status": "attached_to_startup"}}

    def fake_post(url, *, headers=None, json=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return _Response()

    monkeypatch.setattr(http, "post", fake_post)

    result = unify.delegate_to_colleague(
        42,
        instruction="Schedule the renewal summary tomorrow.",
        intent="schedule_task",
        dedupe_key="renewal-summary",
        related_context={"source": "coordinator"},
        api_key="owner-key",
    )

    assert result == {"status": "attached_to_startup"}
    assert captured["url"].endswith("/assistant/42/delegate")
    assert captured["headers"]["Authorization"] == "Bearer owner-key"
    assert captured["json"] == {
        "instruction": "Schedule the renewal summary tomorrow.",
        "intent": "schedule_task",
        "dedupe_key": "renewal-summary",
        "related_context": {"source": "coordinator"},
    }


def test_assistant_lifecycle_round_trips_against_coordinator_preview(
    preview_org: PreviewOrganization,
) -> None:
    org_api_key = preview_org.api_key
    suffix = uuid.uuid4().hex[:10]
    assistant_id: int | None = None

    try:
        created = unify.create_assistant(
            first_name=f"CoordinatorSDK{suffix}",
            surname="Lifecycle",
            config={
                "create_infra": False,
                "is_local": True,
                "timezone": "UTC",
            },
            api_key=org_api_key,
        )
        assistant_id = int(created["agent_id"])

        assert "info" not in created
        assert created["is_coordinator"] is False
        assert created["first_name"] == f"CoordinatorSDK{suffix}"

        listed = unify.list_assistants(
            agent_id=assistant_id,
            list_all_org=True,
            api_key=org_api_key,
        )
        listed_ids = {int(assistant["agent_id"]) for assistant in listed}
        assert assistant_id in listed_ids

        updated = unify.update_assistant_config(
            assistant_id,
            {"first_name": f"Renamed{suffix}"},
            api_key=org_api_key,
        )
        assert int(updated["agent_id"]) == assistant_id
        assert updated["first_name"] == f"Renamed{suffix}"

        with pytest.raises(http.RequestError) as exc_info:
            unify.update_assistant_config(
                assistant_id,
                {"name": "Invalid alias"},
                api_key=org_api_key,
            )
        assert exc_info.value.response.status_code == 422
        assert exc_info.value.response.text

        with pytest.raises(http.RequestError) as missing_exc_info:
            unify.delete_assistant(999999999, api_key=org_api_key)
        assert missing_exc_info.value.response.status_code == 404
        assert missing_exc_info.value.response.text
    finally:
        if assistant_id is not None:
            unify.delete_assistant(assistant_id, api_key=org_api_key)


def test_list_org_members_returns_preview_organization_members(
    preview_org: PreviewOrganization,
) -> None:
    organization_id = preview_org.organization_id
    org_api_key = preview_org.api_key

    members = unify.list_org_members(organization_id, api_key=org_api_key)

    assert members
    assert all(member["organization_id"] == organization_id for member in members)
    assert {"user_id", "organization_id", "role_id"}.issubset(members[0])


def test_list_organizations_returns_role_metadata(
    preview_org: PreviewOrganization,
) -> None:
    organizations = unify.list_organizations(api_key=preview_org.api_key)

    assert organizations
    target = next(
        (org for org in organizations if int(org["id"]) == preview_org.organization_id),
        None,
    )
    assert target is not None
    assert isinstance(target.get("role_id"), int)
    assert isinstance(target.get("role_name"), str)
