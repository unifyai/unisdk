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
        add_space_member,
        cancel_space_invitation,
        create_assistant,
        create_space,
        delete_assistant,
        delete_space,
        invite_assistant_to_space,
        list_assistants,
        list_org_members,
        list_pending_invitations,
        list_space_members,
        list_spaces,
        list_spaces_for_assistant,
        pre_seed_colleague,
        remove_space_member,
        update_assistant_config,
        update_space,
    )

    assert add_space_member is unify.add_space_member
    assert cancel_space_invitation is unify.cancel_space_invitation
    assert create_assistant is unify.create_assistant
    assert create_space is unify.create_space
    assert delete_assistant is unify.delete_assistant
    assert delete_space is unify.delete_space
    assert invite_assistant_to_space is unify.invite_assistant_to_space
    assert list_assistants is unify.list_assistants
    assert list_org_members is unify.list_org_members
    assert list_pending_invitations is unify.list_pending_invitations
    assert list_space_members is unify.list_space_members
    assert list_spaces is unify.list_spaces
    assert list_spaces_for_assistant is unify.list_spaces_for_assistant
    assert pre_seed_colleague is unify.pre_seed_colleague
    assert remove_space_member is unify.remove_space_member
    assert update_assistant_config is unify.update_assistant_config
    assert update_space is unify.update_space
    assert RequestError is http.RequestError

    list_signature = inspect.signature(unify.list_assistants)
    assert "list_all_org" in list_signature.parameters
    assert "organization_id" not in list_signature.parameters

    create_signature = inspect.signature(unify.create_assistant)
    assert "organization_id" not in create_signature.parameters
    assert "is_coordinator" not in create_signature.parameters

    space_signature = inspect.signature(unify.create_space)
    assert "kind" not in space_signature.parameters
    assert "description" in space_signature.parameters

    preseed_signature = inspect.signature(unify.pre_seed_colleague)
    assert list(preseed_signature.parameters) == [
        "target_assistant_id",
        "writes",
        "api_key",
    ]


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
