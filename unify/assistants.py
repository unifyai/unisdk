from typing import Any, Dict, List, Optional, Union

from unify import BASE_URL
from unify.utils import http
from unify.utils.helpers import _create_request_header


def create_assistant(
    *,
    first_name: str,
    surname: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create an assistant in the caller's active workspace.

    Args:
        first_name: The assistant's first name.
        surname: The assistant's surname.
        config: Additional assistant creation fields accepted by the API.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        The created assistant record.
    """
    headers = _create_request_header(api_key)
    body = dict(config or {})
    body.update(
        {
            "first_name": first_name,
            "surname": surname,
        },
    )
    body = {k: v for k, v in body.items() if v is not None}

    response = http.post(f"{BASE_URL}/assistant", headers=headers, json=body)
    return response.json()["info"]


def delete_assistant(
    assistant_id: int,
    *,
    api_key: Optional[str] = None,
) -> Union[Dict[str, Any], str]:
    """
    Delete an assistant that the caller can manage.

    Args:
        assistant_id: The assistant identifier.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        The API response payload.
    """
    headers = _create_request_header(api_key)
    response = http.delete(f"{BASE_URL}/assistant/{assistant_id}", headers=headers)
    return response.json()["info"]


def update_assistant_config(
    assistant_id: int,
    config: Dict[str, Any],
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update an assistant's editable configuration fields.

    Args:
        assistant_id: The assistant identifier.
        config: The assistant update fields to send to the API.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        The updated assistant record.
    """
    headers = _create_request_header(api_key)
    response = http.patch(
        f"{BASE_URL}/assistant/{assistant_id}/config",
        headers=headers,
        json=config,
    )
    return response.json()["info"]


def list_assistants(
    *,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    agent_id: Optional[int] = None,
    list_all_org: bool = False,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List assistants visible to the caller.

    Args:
        phone: Optional phone-number filter.
        email: Optional email filter.
        agent_id: Optional assistant identifier filter.
        list_all_org: When using an organization-scoped key, list every
            assistant in that organization rather than only assistants created
            by the caller.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        Assistant records visible to the caller.
    """
    headers = _create_request_header(api_key)

    params = {
        "phone": phone,
        "email": email,
        "agent_id": agent_id,
    }
    if list_all_org:
        params["list_all_org"] = True
    params = {k: v for k, v in params.items() if v is not None}

    response = http.get(f"{BASE_URL}/assistant", headers=headers, params=params)
    return response.json()["info"]


def delegate_to_colleague(
    target_assistant_id: int,
    *,
    instruction: str,
    intent: str = "general",
    dedupe_key: Optional[str] = None,
    related_context: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Assign asynchronous work to a colleague assistant.

    A successful response is an async delegation receipt. It means the colleague
    has been woken or notified with the assignment, not that the colleague has
    already created durable artifacts or completed the work. The returned payload
    includes ``accepted``, ``completion_status``, ``receipt_type``, and ``message``
    fields that describe this contract, along with dispatch fields such as
    ``status`` and ``activation_id``.

    Args:
        target_assistant_id: Assistant identifier for the colleague that owns the work.
        instruction: Plain-English assignment the colleague should carry out.
        intent: Optional assignment category, for example ``schedule_task``.
        dedupe_key: Optional retry key for avoiding obvious duplicate work.
        related_context: Optional structured context for the colleague.
        api_key: If specified, unify API key to use. Defaults to ``UNIFY_KEY``.

    Returns:
        The API response payload describing accepted async delegation dispatch.
    """
    headers = _create_request_header(api_key)
    body: Dict[str, Any] = {
        "instruction": instruction,
        "intent": intent,
    }
    if dedupe_key is not None:
        body["dedupe_key"] = dedupe_key
    if related_context is not None:
        body["related_context"] = related_context

    response = http.post(
        f"{BASE_URL}/assistant/{target_assistant_id}/delegate",
        headers=headers,
        json=body,
    )
    return response.json()["info"]
