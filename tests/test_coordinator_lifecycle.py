import inspect
import os
import time
import uuid
from typing import Iterator

import pytest

import unify
from unify.utils import http
from unify.utils.helpers import _create_request_header

COORDINATOR_PREVIEW_URL = "https://internal.example.com/v0"


def _headers(api_key: str) -> dict[str, str]:
    return _create_request_header(api_key)


def _require_preview_url() -> str:
    if unify.BASE_URL.rstrip("/") != COORDINATOR_PREVIEW_URL:
        pytest.skip(
            "Coordinator lifecycle tests require ORCHESTRA_URL="
            f"{COORDINATOR_PREVIEW_URL}",
        )
    return COORDINATOR_PREVIEW_URL


def _require_admin_key() -> str:
    admin_key = os.environ.get("COORDINATOR_TEST_ADMIN_KEY") or os.environ.get(
        "ORCHESTRA_ADMIN_KEY",
    )
    if not admin_key:
        pytest.skip("COORDINATOR_TEST_ADMIN_KEY or ORCHESTRA_ADMIN_KEY is required")
    return admin_key


def _require_user_key() -> str:
    user_key = os.environ.get("UNIFY_KEY")
    if not user_key:
        pytest.skip("UNIFY_KEY is required")
    return user_key


def _delete_preview_organization(
    base_url: str,
    organization_id: int,
    api_key: str,
) -> None:
    response = None
    for attempt in range(3):
        response = http.delete(
            f"{base_url}/organizations/{organization_id}",
            headers=_headers(api_key),
            raise_for_status=False,
        )
        if response.status_code in {204, 404}:
            return
        if attempt < 2:
            time.sleep(1)
    assert response is not None
    assert response.status_code in {204, 404}, response.text


@pytest.fixture(scope="module")
def preview_org() -> Iterator[tuple[int, str]]:
    base_url = _require_preview_url()
    admin_key = _require_admin_key()
    user_key = _require_user_key()
    owner = unify.get_user_basic_info()
    org_name = f"Coordinator SDK {uuid.uuid4().hex[:12]}"

    response = http.post(
        f"{base_url}/admin/organizations",
        headers=_headers(admin_key),
        json={
            "name": org_name,
            "creator_user_id": owner["user_id"],
            "timezone": owner.get("timezone") or "UTC",
        },
        timeout=30,
    )
    assert response.status_code == 201, response.text
    organization = response.json()

    try:
        yield int(organization["id"]), organization["api_key"]
    finally:
        _delete_preview_organization(base_url, int(organization["id"]), user_key)


def test_public_coordinator_sdk_exports() -> None:
    from unify import (  # noqa: PLC0415
        RequestError,
        create_assistant,
        delete_assistant,
        list_assistants,
        list_org_members,
        update_assistant_config,
    )

    assert create_assistant is unify.create_assistant
    assert delete_assistant is unify.delete_assistant
    assert list_assistants is unify.list_assistants
    assert list_org_members is unify.list_org_members
    assert update_assistant_config is unify.update_assistant_config
    assert RequestError is http.RequestError

    list_signature = inspect.signature(unify.list_assistants)
    assert "list_all_org" in list_signature.parameters
    assert "organization_id" not in list_signature.parameters

    create_signature = inspect.signature(unify.create_assistant)
    assert "organization_id" not in create_signature.parameters
    assert "is_coordinator" not in create_signature.parameters


def test_assistant_lifecycle_round_trips_against_coordinator_preview(
    preview_org: tuple[int, str],
) -> None:
    _, org_api_key = preview_org
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
    preview_org: tuple[int, str],
) -> None:
    organization_id, org_api_key = preview_org

    members = unify.list_org_members(organization_id, api_key=org_api_key)

    assert members
    assert all(member["organization_id"] == organization_id for member in members)
    assert {"user_id", "organization_id", "role_id"}.issubset(members[0])
