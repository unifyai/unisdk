"""Agent namespace — programmatic interaction with assistants."""

from typing import Any, Dict, Optional

from unify import BASE_URL
from unify.utils import http
from unify.utils.helpers import _create_request_header, _validate_api_key


def send_message(
    assistant_id: int,
    message: str,
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send a programmatic message to an assistant.

    Returns a message status dict containing a ``message_id`` that can be
    polled with :func:`get_message_status` to retrieve the assistant's
    response.

    Args:
        assistant_id: The ID of the assistant to message.
        message: The message content.
        api_key: Optional API key override. Defaults to ``UNIFY_KEY``.

    Returns:
        A dict with keys ``message_id``, ``assistant_id``, ``message``,
        ``status``, ``response``, ``created_at``, ``completed_at``.
    """
    api_key = _validate_api_key(api_key)
    headers = _create_request_header(api_key)
    response = http.post(
        f"{BASE_URL}/messages",
        headers=headers,
        json={"assistant_id": assistant_id, "message": message},
    )
    return response.json()["info"]


def get_message_status(
    message_id: str,
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Poll for the status and response of a previously sent message.

    Returns ``status: "processing"`` while the assistant is working, and
    ``status: "completed"`` (with an optional ``response``) once done.

    Args:
        message_id: The message ID returned by :func:`send_message`.
        api_key: Optional API key override. Defaults to ``UNIFY_KEY``.

    Returns:
        A dict with keys ``message_id``, ``assistant_id``, ``message``,
        ``status``, ``response``, ``created_at``, ``completed_at``.
    """
    api_key = _validate_api_key(api_key)
    headers = _create_request_header(api_key)
    response = http.get(
        f"{BASE_URL}/messages/{message_id}",
        headers=headers,
    )
    return response.json()["info"]
