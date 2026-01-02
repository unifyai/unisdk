from typing import Any, Dict, List, Optional

from unify import BASE_URL
from unify.utils import http
from unify.utils.helpers import _create_request_header


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
