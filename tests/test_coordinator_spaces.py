import sys
import uuid
from collections.abc import Callable
from typing import Iterator

import pytest
from tests.coordinator_helpers import (
    PreviewOrganization,
    PreviewUser,
    managed_preview_organization,
    managed_preview_user,
    require_user_key,
)

import unify
from unify.utils import http


def _record_cleanup_error(
    cleanup_errors: list[Exception],
    cleanup: Callable[[], object],
) -> None:
    try:
        cleanup()
    except Exception as exc:
        cleanup_errors.append(exc)


def _raise_cleanup_error_if_test_passed(cleanup_errors: list[Exception]) -> None:
    if cleanup_errors and sys.exc_info()[0] is None:
        raise cleanup_errors[0]


@pytest.fixture(scope="module")
def preview_org() -> Iterator[PreviewOrganization]:
    with managed_preview_organization() as organization:
        yield organization


@pytest.fixture
def invited_user() -> Iterator[PreviewUser]:
    with managed_preview_user() as user:
        yield user


def test_space_lifecycle_and_membership_round_trips_against_coordinator_preview(
    preview_org: PreviewOrganization,
) -> None:
    suffix = uuid.uuid4().hex[:10]
    assistant_id: int | None = None
    space_id: int | None = None
    membership_added = False

    try:
        assistant = unify.create_assistant(
            first_name=f"SpaceSDK{suffix}",
            surname="Member",
            config={
                "create_infra": False,
                "is_local": True,
                "timezone": "UTC",
            },
            api_key=preview_org.api_key,
        )
        assistant_id = int(assistant["agent_id"])

        space = unify.create_space(
            name=f"Coordinator SDK Space {suffix}",
            organization_id=preview_org.organization_id,
            api_key=preview_org.api_key,
        )
        space_id = int(space["space_id"])
        assert space["organization_id"] == preview_org.organization_id

        listed_by_org = unify.list_spaces(
            organization_id=preview_org.organization_id,
            api_key=preview_org.api_key,
        )
        assert space_id in {int(row["space_id"]) for row in listed_by_org}

        listed_by_owner = unify.list_spaces(
            owner_user_id=space["owner_user_id"],
            api_key=preview_org.api_key,
        )
        assert space_id in {int(row["space_id"]) for row in listed_by_owner}

        renamed = unify.update_space(
            space_id,
            {"name": f"Renamed SDK Space {suffix}"},
            api_key=preview_org.api_key,
        )
        assert renamed["name"] == f"Renamed SDK Space {suffix}"

        with pytest.raises(http.RequestError) as exc_info:
            unify.update_space(
                999999999,
                {"name": "Missing space"},
                api_key=preview_org.api_key,
            )
        assert exc_info.value.response.status_code == 404
        assert exc_info.value.response.text

        membership = unify.add_space_member(
            space_id,
            assistant_id,
            api_key=preview_org.api_key,
        )
        membership_added = True
        assert membership["membership_status"] == "active"
        assert int(membership["assistant_id"]) == assistant_id
        assert int(membership["space_id"]) == space_id

        members = unify.list_space_members(space_id, api_key=preview_org.api_key)
        member_ids = {
            int(member.get("assistant_id", member.get("agent_id")))
            for member in members
        }
        assert assistant_id in member_ids

        assistant_spaces = unify.list_spaces_for_assistant(
            assistant_id,
            api_key=preview_org.api_key,
        )
        assert space_id in {int(row["space_id"]) for row in assistant_spaces}

        remove_response = unify.remove_space_member(
            space_id,
            assistant_id,
            api_key=preview_org.api_key,
        )
        membership_added = False
        assert remove_response == {}

        delete_response = unify.delete_space(space_id, api_key=preview_org.api_key)
        space_id = None
        assert delete_response == {}
    finally:
        cleanup_errors: list[Exception] = []
        if membership_added and space_id is not None and assistant_id is not None:
            _record_cleanup_error(
                cleanup_errors,
                lambda: unify.remove_space_member(
                    space_id,
                    assistant_id,
                    api_key=preview_org.api_key,
                ),
            )
        if space_id is not None:
            _record_cleanup_error(
                cleanup_errors,
                lambda: unify.delete_space(space_id, api_key=preview_org.api_key),
            )
        if assistant_id is not None:
            _record_cleanup_error(
                cleanup_errors,
                lambda: unify.delete_assistant(
                    assistant_id,
                    api_key=preview_org.api_key,
                ),
            )
        _raise_cleanup_error_if_test_passed(cleanup_errors)


def test_invitation_cancel_and_pending_lifecycle(
    invited_user: PreviewUser,
) -> None:
    owner_key = require_user_key()
    suffix = uuid.uuid4().hex[:10]
    assistant_id: int | None = None
    space_id: int | None = None
    invite_id: int | None = None

    try:
        assistant = unify.create_assistant(
            first_name=f"Invitee{suffix}",
            surname="Colleague",
            config={
                "create_infra": False,
                "is_local": True,
                "timezone": "UTC",
            },
            api_key=invited_user.api_key,
        )
        assistant_id = int(assistant["agent_id"])

        space = unify.create_space(
            name=f"Invitation SDK Space {suffix}",
            api_key=owner_key,
        )
        space_id = int(space["space_id"])

        invitation = unify.invite_assistant_to_space(
            space_id,
            assistant_id,
            api_key=owner_key,
        )
        invite_id = int(invitation["invite_id"])
        assert invitation["status"] == "pending"
        assert int(invitation["assistant_id"]) == assistant_id
        assert int(invitation["space_id"]) == space_id

        pending = unify.list_pending_invitations(api_key=invited_user.api_key)
        assert invite_id in {int(row["invite_id"]) for row in pending}

        cancelled_invite_id = invite_id
        cancel_response = unify.cancel_space_invitation(invite_id, api_key=owner_key)
        invite_id = None
        assert cancel_response == {}

        pending_after_cancel = unify.list_pending_invitations(
            api_key=invited_user.api_key,
        )
        assert cancelled_invite_id not in {
            int(row["invite_id"]) for row in pending_after_cancel
        }
    finally:
        cleanup_errors: list[Exception] = []
        if invite_id is not None:
            _record_cleanup_error(
                cleanup_errors,
                lambda: unify.cancel_space_invitation(invite_id, api_key=owner_key),
            )
        if space_id is not None:
            _record_cleanup_error(
                cleanup_errors,
                lambda: unify.delete_space(space_id, api_key=owner_key),
            )
        if assistant_id is not None:
            _record_cleanup_error(
                cleanup_errors,
                lambda: unify.delete_assistant(
                    assistant_id,
                    api_key=invited_user.api_key,
                ),
            )
        _raise_cleanup_error_if_test_passed(cleanup_errors)
