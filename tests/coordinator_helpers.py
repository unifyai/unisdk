import os
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

import pytest

import unify
from unify.utils import http
from unify.utils.helpers import _create_request_header

COORDINATOR_PREVIEW_URL = "https://coordinator.api.staging.internal.saas.unify.ai/v0"


@dataclass(frozen=True)
class PreviewOrganization:
    organization_id: int
    api_key: str


@dataclass(frozen=True)
class PreviewUser:
    user_id: str
    api_key: str


def headers(api_key: str) -> dict[str, str]:
    return _create_request_header(api_key)


def require_preview_url() -> str:
    if unify.BASE_URL.rstrip("/") != COORDINATOR_PREVIEW_URL:
        pytest.skip(
            "Coordinator tests require ORCHESTRA_URL=" f"{COORDINATOR_PREVIEW_URL}",
        )
    return COORDINATOR_PREVIEW_URL


def require_admin_key() -> str:
    admin_key = os.environ.get("COORDINATOR_TEST_ADMIN_KEY") or os.environ.get(
        "ORCHESTRA_ADMIN_KEY",
    )
    if not admin_key:
        pytest.skip("COORDINATOR_TEST_ADMIN_KEY or ORCHESTRA_ADMIN_KEY is required")
    return admin_key


def require_user_key() -> str:
    user_key = os.environ.get("UNIFY_KEY")
    if not user_key:
        pytest.skip("UNIFY_KEY is required")
    return user_key


def delete_preview_organization(
    base_url: str,
    organization_id: int,
    api_key: str,
) -> None:
    response = None
    for attempt in range(3):
        response = http.delete(
            f"{base_url}/organizations/{organization_id}",
            headers=headers(api_key),
            raise_for_status=False,
            timeout=30,
        )
        if response.status_code in {204, 404}:
            return
        if attempt < 2:
            time.sleep(1)
    assert response is not None
    assert response.status_code in {204, 404}, response.text


@contextmanager
def managed_preview_organization() -> Iterator[PreviewOrganization]:
    base_url = require_preview_url()
    admin_key = require_admin_key()
    user_key = require_user_key()
    owner = unify.get_user_basic_info()
    org_name = f"Coordinator SDK {uuid.uuid4().hex[:12]}"

    response = http.post(
        f"{base_url}/admin/organizations",
        headers=headers(admin_key),
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
        yield PreviewOrganization(
            organization_id=int(organization["id"]),
            api_key=organization["api_key"],
        )
    finally:
        delete_preview_organization(base_url, int(organization["id"]), user_key)


@contextmanager
def managed_preview_user() -> Iterator[PreviewUser]:
    base_url = require_preview_url()
    admin_key = require_admin_key()
    suffix = uuid.uuid4().hex[:12]
    email = f"sdk-team-invite-{suffix}@unify.ai"
    user_id = None

    response = http.post(
        f"{base_url}/admin/user",
        headers=headers(admin_key),
        json={
            "email": email,
            "name": "SDK",
            "last_name": "Invite",
            "timezone": "UTC",
        },
        timeout=30,
    )
    assert response.status_code == 200, response.text
    user_id = response.json()["id"]

    try:
        details = http.get(
            f"{base_url}/admin/user/by-user-id",
            headers=headers(admin_key),
            params={"user_id": user_id},
            timeout=30,
        )
        assert details.status_code == 200, details.text

        yield PreviewUser(
            user_id=user_id,
            api_key=details.json()["api_key"],
        )
    finally:
        if user_id is not None:
            response = http.delete(
                f"{base_url}/admin/user",
                headers=headers(admin_key),
                params={"user_id": user_id, "force": True},
                raise_for_status=False,
                timeout=30,
            )
            assert response.status_code in {200, 404}, response.text
