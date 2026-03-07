import uuid

import pytest
import unify
import unify.agent
from unify.utils import http
from unify.utils.helpers import _create_request_header, _validate_api_key


@pytest.fixture
def assistant_id():
    """Create a test assistant and clean up after."""
    suffix = uuid.uuid4().hex[:8]
    headers = _create_request_header(_validate_api_key(None))
    response = http.post(
        f"{unify.BASE_URL}/assistant",
        headers=headers,
        json={
            "first_name": f"AgentSDK{suffix}",
            "surname": "Test",
            "create_infra": False,
            "is_local": True,
        },
    )
    aid = int(response.json()["info"]["agent_id"])
    yield aid
    http.delete(f"{unify.BASE_URL}/assistant/{aid}", headers=headers)


def test_send_message(assistant_id):
    result = unify.agent.send_message(assistant_id, "Hello from SDK")
    assert "message_id" in result
    assert result["status"] == "processing"
    assert result["assistant_id"] == assistant_id
    assert result["message"] == "Hello from SDK"
    assert result["response"] is None


def test_get_message_status(assistant_id):
    sent = unify.agent.send_message(assistant_id, "Poll me")
    message_id = sent["message_id"]

    status = unify.agent.get_message_status(message_id)
    assert status["message_id"] == message_id
    assert status["status"] == "processing"
    assert status["message"] == "Poll me"
    assert status["assistant_id"] == assistant_id
    assert status["created_at"] is not None


def test_get_nonexistent_message():
    with pytest.raises(http.RequestError):
        unify.agent.get_message_status("00000000-0000-0000-0000-000000000000")


def test_send_to_nonexistent_assistant():
    with pytest.raises(http.RequestError):
        unify.agent.send_message(999999, "Should fail")


def test_send_empty_message(assistant_id):
    with pytest.raises(http.RequestError):
        unify.agent.send_message(assistant_id, "")


def test_multiple_messages_independent(assistant_id):
    ids = []
    for msg in ["First", "Second", "Third"]:
        result = unify.agent.send_message(assistant_id, msg)
        ids.append(result["message_id"])

    assert len(set(ids)) == 3

    for mid in ids:
        status = unify.agent.get_message_status(mid)
        assert status["status"] == "processing"
