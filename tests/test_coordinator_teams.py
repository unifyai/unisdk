import sys
import uuid
from collections.abc import Callable

import pytest

import unisdk
from unisdk.utils import http


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


def test_team_lifecycle_and_membership_round_trips(coordinator_org) -> None:
    suffix = uuid.uuid4().hex[:10]
    assistant_id: int | None = None
    team_id: int | None = None
    membership_added = False
    organization_id = coordinator_org.organization_id

    try:
        assistant = unisdk.create_assistant(
            first_name=f"TeamSDK{suffix}",
            surname="Member",
            config={
                "create_infra": False,
                "is_local": True,
                "timezone": "UTC",
            },
            api_key=coordinator_org.api_key,
        )
        assistant_id = int(assistant["agent_id"])

        team = unisdk.create_team(
            organization_id,
            name=f"Coordinator SDK Team {suffix}",
            description="SDK integration team for membership lifecycle coverage.",
            api_key=coordinator_org.api_key,
        )
        team_id = int(team["team_id"])
        assert int(team["organization_id"]) == organization_id

        listed_by_org = unisdk.list_teams(
            organization_id,
            api_key=coordinator_org.api_key,
        )
        assert team_id in {int(row["team_id"]) for row in listed_by_org}

        renamed = unisdk.update_team(
            organization_id,
            team_id,
            {"name": f"Renamed SDK Team {suffix}"},
            api_key=coordinator_org.api_key,
        )
        assert renamed["name"] == f"Renamed SDK Team {suffix}"

        with pytest.raises(http.RequestError) as exc_info:
            unisdk.update_team(
                organization_id,
                999999999,
                {"name": "Missing team"},
                api_key=coordinator_org.api_key,
            )
        assert exc_info.value.response.status_code == 404
        assert exc_info.value.response.text

        membership = unisdk.add_team_member(
            organization_id,
            team_id,
            assistant_id=assistant_id,
            api_key=coordinator_org.api_key,
        )
        membership_added = True
        assert membership["membership_status"] == "active"
        assert int(membership["assistant_id"]) == assistant_id
        assert int(membership["team_id"]) == team_id

        members = unisdk.list_team_members(
            organization_id,
            team_id,
            api_key=coordinator_org.api_key,
        )
        member_ids = {
            int(member.get("assistant_id", member.get("agent_id")))
            for member in members
        }
        assert assistant_id in member_ids

        assistant_teams = unisdk.list_teams_for_assistant(
            assistant_id,
            api_key=coordinator_org.api_key,
        )
        assert team_id in {int(row["team_id"]) for row in assistant_teams}

        remove_response = unisdk.remove_team_member(
            organization_id,
            team_id,
            assistant_id,
            api_key=coordinator_org.api_key,
        )
        membership_added = False
        assert remove_response == {}

        delete_response = unisdk.delete_team(
            organization_id,
            team_id,
            api_key=coordinator_org.api_key,
        )
        team_id = None
        assert delete_response == {}
    finally:
        cleanup_errors: list[Exception] = []
        if membership_added and team_id is not None and assistant_id is not None:
            _record_cleanup_error(
                cleanup_errors,
                lambda: unisdk.remove_team_member(
                    organization_id,
                    team_id,
                    assistant_id,
                    api_key=coordinator_org.api_key,
                ),
            )
        if team_id is not None:
            _record_cleanup_error(
                cleanup_errors,
                lambda: unisdk.delete_team(
                    organization_id,
                    team_id,
                    api_key=coordinator_org.api_key,
                ),
            )
        if assistant_id is not None:
            _record_cleanup_error(
                cleanup_errors,
                lambda: unisdk.delete_assistant(
                    assistant_id,
                    api_key=coordinator_org.api_key,
                ),
            )
        _raise_cleanup_error_if_test_passed(cleanup_errors)


def test_member_target_add_for_org_member_is_idempotent(coordinator_org) -> None:
    suffix = uuid.uuid4().hex[:10]
    team_id: int | None = None
    member_assistant_id: int | None = None
    organization_id = coordinator_org.organization_id

    try:
        team = unisdk.create_team(
            organization_id,
            name=f"Member Target SDK Team {suffix}",
            description="SDK integration team for member-target add idempotency coverage.",
            api_key=coordinator_org.api_key,
        )
        team_id = int(team["team_id"])

        owner_user_id = unisdk.get_user_basic_info(api_key=coordinator_org.api_key)[
            "user_id"
        ]
        first_add = unisdk.add_team_member(
            organization_id,
            team_id,
            member_user_id=owner_user_id,
            api_key=coordinator_org.api_key,
        )
        assert first_add["membership_status"] == "active"
        assert int(first_add["team_id"]) == team_id
        member_assistant_id = int(first_add["assistant_id"])

        second_add = unisdk.add_team_member(
            organization_id,
            team_id,
            member_user_id=owner_user_id,
            api_key=coordinator_org.api_key,
        )
        assert second_add["membership_status"] == "active"
        assert int(second_add["assistant_id"]) == member_assistant_id

        members = unisdk.list_team_members(
            organization_id,
            team_id,
            api_key=coordinator_org.api_key,
        )
        member_ids = {
            int(member.get("assistant_id", member.get("agent_id")))
            for member in members
        }
        assert member_assistant_id in member_ids

        remove_response = unisdk.remove_team_member(
            organization_id,
            team_id,
            member_assistant_id,
            api_key=coordinator_org.api_key,
        )
        member_assistant_id = None
        assert remove_response == {}
    finally:
        cleanup_errors: list[Exception] = []
        if member_assistant_id is not None and team_id is not None:
            _record_cleanup_error(
                cleanup_errors,
                lambda: unisdk.remove_team_member(
                    organization_id,
                    team_id,
                    member_assistant_id,
                    api_key=coordinator_org.api_key,
                ),
            )
        if team_id is not None:
            _record_cleanup_error(
                cleanup_errors,
                lambda: unisdk.delete_team(
                    organization_id,
                    team_id,
                    api_key=coordinator_org.api_key,
                ),
            )
        _raise_cleanup_error_if_test_passed(cleanup_errors)
