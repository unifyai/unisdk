"""
Tests for provider-specific preprocessing of messages.
"""

import json

from unify.universal_api.utils.provider_preprocessing import (
    _combine_adjacent_user_messages,
    _is_anthropic_provider,
    _move_system_messages_to_front,
    apply_provider_preprocessing,
    preprocess_messages_for_anthropic,
    preprocess_messages_for_provider,
)


class TestIsAnthropicProvider:
    """Tests for _is_anthropic_provider function."""

    def test_anthropic_provider(self):
        assert _is_anthropic_provider("anthropic") is True

    def test_non_anthropic_provider(self):
        assert _is_anthropic_provider("openai") is False

    def test_anthropic_fallback_chain_first(self):
        """Anthropic as first provider in fallback chain."""
        assert _is_anthropic_provider("anthropic->openai") is True

    def test_anthropic_fallback_chain_not_first(self):
        """Anthropic not as first provider in fallback chain."""
        assert _is_anthropic_provider("openai->anthropic") is False

    def test_none_provider(self):
        assert _is_anthropic_provider(None) is False

    def test_empty_string(self):
        assert _is_anthropic_provider("") is False


class TestMoveSystemMessagesToFront:
    """Tests for _move_system_messages_to_front function."""

    def test_no_system_messages(self):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]
        result = _move_system_messages_to_front(messages)
        assert result == messages

    def test_system_already_at_front(self):
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]
        result = _move_system_messages_to_front(messages)
        assert result == messages

    def test_single_system_in_middle(self):
        messages = [
            {"role": "user", "content": "A"},
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "B"},
        ]
        result = _move_system_messages_to_front(messages)
        expected = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "A"},
            {"role": "user", "content": "B"},
        ]
        assert result == expected

    def test_multiple_system_messages_scattered(self):
        """sys1 -> user1 -> sys2 -> user2 becomes sys1 -> sys2 -> user1 -> user2"""
        messages = [
            {"role": "system", "content": "sys1"},
            {"role": "user", "content": "user1"},
            {"role": "system", "content": "sys2"},
            {"role": "user", "content": "user2"},
        ]
        result = _move_system_messages_to_front(messages)
        expected = [
            {"role": "system", "content": "sys1"},
            {"role": "system", "content": "sys2"},
            {"role": "user", "content": "user1"},
            {"role": "user", "content": "user2"},
        ]
        assert result == expected

    def test_preserves_system_order(self):
        """System messages should maintain their relative order."""
        messages = [
            {"role": "user", "content": "user1"},
            {"role": "system", "content": "sys1"},
            {"role": "assistant", "content": "assistant1"},
            {"role": "system", "content": "sys2"},
            {"role": "user", "content": "user2"},
            {"role": "system", "content": "sys3"},
        ]
        result = _move_system_messages_to_front(messages)
        # System messages should be in order: sys1, sys2, sys3
        assert result[0] == {"role": "system", "content": "sys1"}
        assert result[1] == {"role": "system", "content": "sys2"}
        assert result[2] == {"role": "system", "content": "sys3"}
        # Non-system messages should preserve order
        assert result[3] == {"role": "user", "content": "user1"}
        assert result[4] == {"role": "assistant", "content": "assistant1"}
        assert result[5] == {"role": "user", "content": "user2"}

    def test_empty_list(self):
        result = _move_system_messages_to_front([])
        assert result == []


class TestCombineAdjacentUserMessages:
    """Tests for _combine_adjacent_user_messages function."""

    def test_no_adjacent_users(self):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "Bye"},
        ]
        result = _combine_adjacent_user_messages(messages)
        assert result == messages

    def test_two_adjacent_users(self):
        messages = [
            {"role": "user", "content": "A"},
            {"role": "user", "content": "B"},
        ]
        result = _combine_adjacent_user_messages(messages)
        assert len(result) == 1
        assert result[0]["role"] == "user"
        # Parse the JSON content
        content_dict = json.loads(result[0]["content"])
        assert content_dict["role"] == "user"
        assert content_dict["content"] == [
            {"type": "text", "text": "A"},
            {"type": "text", "text": "B"},
        ]

    def test_three_adjacent_users(self):
        messages = [
            {"role": "user", "content": "A"},
            {"role": "user", "content": "B"},
            {"role": "user", "content": "C"},
        ]
        result = _combine_adjacent_user_messages(messages)
        assert len(result) == 1
        content_dict = json.loads(result[0]["content"])
        assert content_dict["content"] == [
            {"type": "text", "text": "A"},
            {"type": "text", "text": "B"},
            {"type": "text", "text": "C"},
        ]

    def test_adjacent_users_after_assistant(self):
        messages = [
            {"role": "assistant", "content": "Hello"},
            {"role": "user", "content": "A"},
            {"role": "user", "content": "B"},
        ]
        result = _combine_adjacent_user_messages(messages)
        assert len(result) == 2
        assert result[0] == {"role": "assistant", "content": "Hello"}
        content_dict = json.loads(result[1]["content"])
        assert content_dict["content"] == [
            {"type": "text", "text": "A"},
            {"type": "text", "text": "B"},
        ]

    def test_multiple_groups_of_adjacent_users(self):
        messages = [
            {"role": "user", "content": "A"},
            {"role": "user", "content": "B"},
            {"role": "assistant", "content": "response"},
            {"role": "user", "content": "C"},
            {"role": "user", "content": "D"},
        ]
        result = _combine_adjacent_user_messages(messages)
        assert len(result) == 3
        # First combined group
        content1 = json.loads(result[0]["content"])
        assert content1["content"] == [
            {"type": "text", "text": "A"},
            {"type": "text", "text": "B"},
        ]
        # Assistant message
        assert result[1] == {"role": "assistant", "content": "response"}
        # Second combined group
        content2 = json.loads(result[2]["content"])
        assert content2["content"] == [
            {"type": "text", "text": "C"},
            {"type": "text", "text": "D"},
        ]

    def test_empty_list(self):
        result = _combine_adjacent_user_messages([])
        assert result == []

    def test_single_user_not_combined(self):
        messages = [
            {"role": "user", "content": "alone"},
        ]
        result = _combine_adjacent_user_messages(messages)
        assert result == messages

    def test_json_format_is_indented(self):
        """Verify the JSON output uses indent=4."""
        messages = [
            {"role": "user", "content": "A"},
            {"role": "user", "content": "B"},
        ]
        result = _combine_adjacent_user_messages(messages)
        content_str = result[0]["content"]
        # Check that it's indented (contains newlines and spaces)
        assert "\n" in content_str
        assert "    " in content_str  # 4-space indent


class TestPreprocessMessagesForAnthropic:
    """Tests for the combined Anthropic preprocessing."""

    def test_system_move_then_user_combine(self):
        """Test that system messages move first, then adjacent users are combined."""
        messages = [
            {"role": "system", "content": "sys1"},
            {"role": "user", "content": "A"},
            {"role": "system", "content": "sys2"},
            {"role": "user", "content": "B"},
        ]
        result = preprocess_messages_for_anthropic(messages)

        # After system move: sys1 -> sys2 -> A -> B
        # After user combine: sys1 -> sys2 -> combined(A,B)
        assert len(result) == 3
        assert result[0] == {"role": "system", "content": "sys1"}
        assert result[1] == {"role": "system", "content": "sys2"}

        content_dict = json.loads(result[2]["content"])
        assert content_dict["content"] == [
            {"type": "text", "text": "A"},
            {"type": "text", "text": "B"},
        ]

    def test_does_not_modify_original(self):
        """Preprocessing should return a new list, not modify the original."""
        messages = [
            {"role": "user", "content": "A"},
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "B"},
        ]
        original_messages = [msg.copy() for msg in messages]

        result = preprocess_messages_for_anthropic(messages)

        # Original should be unchanged
        assert messages == original_messages
        # Result should be different
        assert result != messages

    def test_complex_conversation(self):
        """Test a more realistic conversation flow."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "What is 1+1?"},
            {"role": "user", "content": "Also, what is 2+2?"},
        ]
        result = preprocess_messages_for_anthropic(messages)

        # Expected order after preprocessing:
        # sys("You are...") -> sys("Be concise") -> user("Hello") ->
        # assistant("Hi there!") -> combined_user(1+1, 2+2)
        assert len(result) == 5
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "You are a helpful assistant."
        assert result[1]["role"] == "system"
        assert result[1]["content"] == "Be concise."
        assert result[2]["role"] == "user"
        assert result[2]["content"] == "Hello"
        assert result[3]["role"] == "assistant"
        assert result[4]["role"] == "user"

        content_dict = json.loads(result[4]["content"])
        assert len(content_dict["content"]) == 2


class TestPreprocessMessagesForProvider:
    """Tests for the provider dispatch function."""

    def test_anthropic_preprocessing_applied(self):
        messages = [
            {"role": "user", "content": "A"},
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "B"},
        ]
        result = preprocess_messages_for_provider(messages, "anthropic")

        # System should be moved to front
        assert result[0]["role"] == "system"
        # Users should be combined
        content = json.loads(result[1]["content"])
        assert len(content["content"]) == 2

    def test_non_anthropic_no_preprocessing(self):
        messages = [
            {"role": "user", "content": "A"},
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "B"},
        ]
        result = preprocess_messages_for_provider(messages, "openai")

        # Should return a copy but unchanged order
        assert result == messages
        assert result is not messages  # Should be a copy

    def test_none_provider_no_preprocessing(self):
        messages = [
            {"role": "user", "content": "A"},
            {"role": "system", "content": "sys"},
        ]
        result = preprocess_messages_for_provider(messages, None)
        assert result == messages


class TestApplyProviderPreprocessing:
    """Tests for apply_provider_preprocessing on kw dict."""

    def test_modifies_messages_in_kw(self):
        kw = {
            "model": "claude@anthropic",
            "messages": [
                {"role": "user", "content": "A"},
                {"role": "system", "content": "sys"},
                {"role": "user", "content": "B"},
            ],
        }
        result = apply_provider_preprocessing(kw, "anthropic")

        # Should be same dict reference
        assert result is kw
        # Messages should be preprocessed
        assert kw["messages"][0]["role"] == "system"

    def test_handles_empty_messages(self):
        kw = {"model": "claude@anthropic", "messages": []}
        result = apply_provider_preprocessing(kw, "anthropic")
        assert result["messages"] == []

    def test_handles_missing_messages(self):
        kw = {"model": "claude@anthropic"}
        result = apply_provider_preprocessing(kw, "anthropic")
        assert "messages" not in result

    def test_handles_none_messages(self):
        kw = {"model": "claude@anthropic", "messages": None}
        result = apply_provider_preprocessing(kw, "anthropic")
        assert result["messages"] is None

    def test_non_anthropic_preserves_order(self):
        kw = {
            "model": "gpt-4@openai",
            "messages": [
                {"role": "user", "content": "A"},
                {"role": "system", "content": "sys"},
            ],
        }
        original_messages = [msg.copy() for msg in kw["messages"]]
        apply_provider_preprocessing(kw, "openai")

        assert kw["messages"] == original_messages


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_all_system_messages(self):
        messages = [
            {"role": "system", "content": "sys1"},
            {"role": "system", "content": "sys2"},
            {"role": "system", "content": "sys3"},
        ]
        result = preprocess_messages_for_anthropic(messages)
        assert result == messages

    def test_all_user_messages(self):
        messages = [
            {"role": "user", "content": "A"},
            {"role": "user", "content": "B"},
            {"role": "user", "content": "C"},
        ]
        result = preprocess_messages_for_anthropic(messages)
        assert len(result) == 1
        content = json.loads(result[0]["content"])
        assert len(content["content"]) == 3

    def test_alternating_user_assistant(self):
        messages = [
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
            {"role": "user", "content": "Q2"},
            {"role": "assistant", "content": "A2"},
        ]
        result = preprocess_messages_for_anthropic(messages)
        # No adjacent users, no system to move - should be unchanged
        assert result == messages

    def test_empty_content_handling(self):
        messages = [
            {"role": "user", "content": ""},
            {"role": "user", "content": "B"},
        ]
        result = preprocess_messages_for_anthropic(messages)
        content = json.loads(result[0]["content"])
        assert content["content"][0]["text"] == ""
        assert content["content"][1]["text"] == "B"

    def test_fallback_chain_anthropic_first(self):
        """Test with Anthropic as first in fallback chain."""
        messages = [
            {"role": "user", "content": "A"},
            {"role": "system", "content": "sys"},
        ]
        result = preprocess_messages_for_provider(messages, "anthropic->openai")
        # Should apply Anthropic preprocessing
        assert result[0]["role"] == "system"

    def test_fallback_chain_anthropic_not_first(self):
        """Test with Anthropic not first in fallback chain."""
        messages = [
            {"role": "user", "content": "A"},
            {"role": "system", "content": "sys"},
        ]
        result = preprocess_messages_for_provider(messages, "openai->anthropic")
        # Should NOT apply Anthropic preprocessing (uses first provider)
        assert result[0]["role"] == "user"
