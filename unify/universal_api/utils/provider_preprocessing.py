"""
Provider-specific preprocessing for messages before sending to the API.

This module contains preprocessing rules that are applied immediately before
sending requests to specific providers. The preprocessing happens:
- After all Unify/AsyncUnify manipulation and stateful handling
- Before the cache check
- On a copy of the messages (not preserved in client.messages)
"""

import copy
import json
from typing import Any, Dict, List, Optional


def _is_anthropic_provider(provider: Optional[str]) -> bool:
    """
    Check if the provider string indicates an Anthropic provider.

    Handles regular providers (e.g., "anthropic") and fallback chains
    (e.g., "anthropic->openai").

    Args:
        provider: The provider string from the endpoint.

    Returns:
        True if this is an Anthropic provider.
    """
    if provider is None:
        return False
    # Check the first provider in case of fallback chain
    first_provider = provider.split("->")[0].strip()
    return first_provider == "anthropic"


def _move_system_messages_to_front(
    messages: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Move all system messages to the beginning of the messages list,
    preserving their relative order among themselves.

    Example: sys1 -> user1 -> sys2 -> user2 becomes sys1 -> sys2 -> user1 -> user2

    Args:
        messages: List of message dictionaries.

    Returns:
        New list with system messages moved to the front.
    """
    system_messages = []
    non_system_messages = []

    for msg in messages:
        if msg.get("role") == "system":
            system_messages.append(msg)
        else:
            non_system_messages.append(msg)

    return system_messages + non_system_messages


def _combine_adjacent_user_messages(
    messages: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Combine adjacent user messages into a single message with content array format.

    The combined message content is formatted as a JSON string representing
    the Anthropic content array format:

    {
        "role": "user",
        "content": [
            {"type": "text", "text": "{x}"},
            {"type": "text", "text": "{y}"}
        ]
    }

    Args:
        messages: List of message dictionaries.

    Returns:
        New list with adjacent user messages combined.
    """
    if not messages:
        return []

    result = []
    i = 0

    while i < len(messages):
        current_msg = messages[i]

        if current_msg.get("role") != "user":
            result.append(current_msg)
            i += 1
            continue

        # Collect all adjacent user messages
        adjacent_user_contents = []
        while i < len(messages) and messages[i].get("role") == "user":
            content = messages[i].get("content", "")
            adjacent_user_contents.append(content)
            i += 1

        if len(adjacent_user_contents) == 1:
            # Only one user message, keep it as is
            result.append(current_msg)
        else:
            # Multiple adjacent user messages - combine them
            content_array = [
                {"type": "text", "text": content} for content in adjacent_user_contents
            ]
            combined_content = json.dumps(
                {
                    "role": "user",
                    "content": content_array,
                },
                indent=4,
            )
            result.append(
                {
                    "role": "user",
                    "content": combined_content,
                },
            )

    return result


def preprocess_messages_for_anthropic(
    messages: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Apply Anthropic-specific preprocessing to messages.

    This performs two transformations:
    1. Move all system messages to the beginning of the list
    2. Combine adjacent user messages into content array format

    Args:
        messages: List of message dictionaries.

    Returns:
        Preprocessed messages (a new list, original is not modified).
    """
    # Deep copy to avoid modifying the original
    messages = copy.deepcopy(messages)

    # Step 1: Move system messages to front
    messages = _move_system_messages_to_front(messages)

    # Step 2: Combine adjacent user messages
    messages = _combine_adjacent_user_messages(messages)

    return messages


def preprocess_messages_for_provider(
    messages: List[Dict[str, Any]],
    provider: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Apply provider-specific preprocessing to messages.

    This is the main entry point for message preprocessing. It dispatches
    to the appropriate provider-specific function based on the provider.

    Args:
        messages: List of message dictionaries.
        provider: The provider string (e.g., "anthropic", "openai").

    Returns:
        Preprocessed messages (a new list, original is not modified).
    """
    if _is_anthropic_provider(provider):
        return preprocess_messages_for_anthropic(messages)

    # No preprocessing for other providers - return a copy to be consistent
    return copy.deepcopy(messages)


def apply_provider_preprocessing(
    kw: Dict[str, Any],
    provider: Optional[str],
) -> Dict[str, Any]:
    """
    Apply provider-specific preprocessing to the keyword arguments dict.

    This modifies the 'messages' key in the kw dict if preprocessing is needed.
    The kw dict is modified in place and also returned.

    Args:
        kw: The keyword arguments dictionary containing 'messages'.
        provider: The provider string.

    Returns:
        The modified kw dict.
    """
    if "messages" in kw and kw["messages"]:
        kw["messages"] = preprocess_messages_for_provider(kw["messages"], provider)
    return kw
