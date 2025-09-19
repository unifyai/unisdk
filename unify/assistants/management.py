from typing import Any, Dict, List, Optional, Union

from unify import BASE_URL
from unify.utils import http
from unify.utils.helpers import _create_request_header


def create_assistant(
    *,
    first_name: Optional[str] = None,
    surname: Optional[str] = None,
    age: Optional[int] = None,
    weekly_limit: Optional[float] = None,
    max_parallel: Optional[int] = None,
    region: Optional[str] = None,
    profile_photo: Optional[str] = None,
    profile_video: Optional[str] = None,
    about: Optional[str] = None,
    country: Optional[str] = None,
    email: Optional[str] = None,
    voice_id: Optional[str] = None,
    user_phone: Optional[str] = None,
    user_whatsapp_number: Optional[str] = None,
    create_infra: Optional[bool] = None,
    phone: Optional[str] = None,
    pre_hire_chat: Optional[List[Dict[str, Any]]] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new assistant. Returns the API response JSON.
    """
    headers = _create_request_header(api_key)

    payload = {
        "first_name": first_name,
        "surname": surname,
        "age": age,
        "weekly_limit": weekly_limit,
        "max_parallel": max_parallel,
        "region": region,
        "profile_photo": profile_photo,
        "profile_video": profile_video,
        "about": about,
        "country": country,
        "email": email,
        "voice_id": voice_id,
        "user_phone": user_phone,
        "user_whatsapp_number": user_whatsapp_number,
        "create_infra": create_infra,
        "phone": phone,
        "pre_hire_chat": pre_hire_chat,
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    response = http.post(f"{BASE_URL}/assistant", headers=headers, json=payload)
    return response.json()["info"]


def list_assistants(
    *,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List all assistants. Returns the API response JSON.

    Optional filters: phone, email.
    """
    headers = _create_request_header(api_key)

    params = {"phone": phone, "email": email}
    params = {k: v for k, v in params.items() if v is not None}

    response = http.get(f"{BASE_URL}/assistant", headers=headers, params=params)
    return response.json()["info"]


def update_assistant(
    assistant_id: Union[int, str],
    *,
    first_name: Optional[str] = None,
    surname: Optional[str] = None,
    age: Optional[int] = None,
    weekly_limit: Optional[float] = None,
    max_parallel: Optional[int] = None,
    region: Optional[str] = None,
    profile_photo: Optional[str] = None,
    profile_video: Optional[str] = None,
    about: Optional[str] = None,
    country: Optional[str] = None,
    email: Optional[str] = None,
    voice_id: Optional[str] = None,
    user_phone: Optional[str] = None,
    user_whatsapp_number: Optional[str] = None,
    create_infra: Optional[bool] = None,
    phone: Optional[str] = None,
    pre_hire_chat: Optional[List[Dict[str, Any]]] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update an assistant configuration. Returns the API response JSON.
    """
    headers = _create_request_header(api_key)

    payload = {
        "first_name": first_name,
        "surname": surname,
        "age": age,
        "weekly_limit": weekly_limit,
        "max_parallel": max_parallel,
        "region": region,
        "profile_photo": profile_photo,
        "profile_video": profile_video,
        "about": about,
        "country": country,
        "email": email,
        "voice_id": voice_id,
        "user_phone": user_phone,
        "user_whatsapp_number": user_whatsapp_number,
        "create_infra": create_infra,
        "phone": phone,
        "pre_hire_chat": pre_hire_chat,
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    response = http.patch(
        f"{BASE_URL}/assistant/{assistant_id}/config",
        headers=headers,
        json=payload,
    )
    return response.json()


def delete_assistant(
    assistant_id: Union[int, str],
    *,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Delete an assistant by id. Returns the API response JSON.
    """
    headers = _create_request_header(api_key)

    response = http.delete(
        f"{BASE_URL}/assistant/{assistant_id}",
        headers=headers,
    )
    return response.json()
