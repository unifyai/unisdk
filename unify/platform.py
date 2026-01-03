"""Platform API utilities for interacting with the Unify platform."""

from typing import Optional

from unify import BASE_URL
from unify.utils import http
from unify.utils.helpers import _create_request_header


def deduct_credits(
    amount: float,
    *,
    api_key: Optional[str] = None,
) -> dict:
    """
    Deduct credits from the authenticated user's account.

    The amount must be positive and cannot exceed the user's available credits.

    Args:
        amount: The amount of credits to deduct (must be > 0).
        api_key: If specified, unify API key to be used. Defaults
            to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A dict with keys:
            - previous_credits: Credits before deduction
            - deducted: Amount deducted
            - current_credits: Credits after deduction

    Raises:
        RequestError: If the request fails (e.g., insufficient credits,
            invalid amount, or authentication error).
    """
    headers = _create_request_header(api_key)
    response = http.post(
        f"{BASE_URL}/credits/deduct",
        headers=headers,
        json={"amount": amount},
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
