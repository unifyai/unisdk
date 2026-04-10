"""Platform API utilities for interacting with the Unify platform."""

from typing import Optional

from unify import BASE_URL
from unify.utils import http
from unify.utils.helpers import _create_request_header


def deduct_credits(
    amount: float,
    *,
    category: Optional[str] = None,
    assistant_id: Optional[int] = None,
    user_id: Optional[str] = None,
    organization_id: Optional[int] = None,
    description: Optional[str] = None,
    detail: Optional[dict] = None,
    api_key: Optional[str] = None,
) -> dict:
    """
    Deduct credits from the authenticated user's account.

    The amount must be positive. The balance is allowed to go negative
    (overdraft) so that downstream spending-limit hooks can detect and
    block further usage.

    Args:
        amount: The amount of credits to deduct (must be > 0).
        category: Ledger category (e.g. ``"llm"``, ``"media"``, ``"setup"``).
        assistant_id: Assistant that incurred the cost.
        user_id: User who triggered the cost (for org member attribution).
        organization_id: Organization that owns the billing account.
        description: Human-readable description of the charge.
        detail: Arbitrary metadata dict (model, tokens, etc.).
        api_key: If specified, unify API key to be used. Defaults
            to the value in the ``UNIFY_KEY`` environment variable.

    Returns:
        A dict with keys:
            - previous_credits: Credits before deduction
            - deducted: Amount deducted
            - current_credits: Credits after deduction (may be negative)

    Raises:
        RequestError: If the request fails (e.g., invalid amount
            or authentication error).
    """
    headers = _create_request_header(api_key)
    body: dict = {"amount": amount}
    if category is not None:
        body["category"] = category
    if assistant_id is not None:
        body["assistant_id"] = assistant_id
    if user_id is not None:
        body["user_id"] = user_id
    if organization_id is not None:
        body["organization_id"] = organization_id
    if description is not None:
        body["description"] = description
    if detail is not None:
        body["detail"] = detail
    response = http.post(
        f"{BASE_URL}/credits/deduct",
        headers=headers,
        json=body,
    )
    return response.json()


def get_user_basic_info(*, api_key: Optional[str] = None):
    """
    Get basic information for the authenticated user.

    Args:
        api_key: If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        The basic information for the authenticated user.
    """
    headers = _create_request_header(api_key)
    response = http.get(f"{BASE_URL}/user/basic-info", headers=headers)
    return response.json()
