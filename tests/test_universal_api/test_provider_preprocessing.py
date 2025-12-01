"""Tests for provider-specific preprocessing of messages."""

import json

from unify.universal_api.utils.provider_preprocessing import (
    CONCURRENT_USER_MESSAGES_EXPLANATION,
    _combine_adjacent_user_messages,
    _move_system_messages_to_front,
    apply_provider_preprocessing,
)


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

    def test_preserves_relative_order(self):
        messages = [
            {"role": "user", "content": "user1"},
            {"role": "system", "content": "sys1"},
            {"role": "assistant", "content": "assistant1"},
            {"role": "system", "content": "sys2"},
            {"role": "user", "content": "user2"},
            {"role": "system", "content": "sys3"},
        ]
        result = _move_system_messages_to_front(messages)
        assert result[0] == {"role": "system", "content": "sys1"}
        assert result[1] == {"role": "system", "content": "sys2"}
        assert result[2] == {"role": "system", "content": "sys3"}
        assert result[3] == {"role": "user", "content": "user1"}
        assert result[4] == {"role": "assistant", "content": "assistant1"}
        assert result[5] == {"role": "user", "content": "user2"}

    def test_empty_list(self):
        assert _move_system_messages_to_front([]) == []


class TestCombineAdjacentUserMessages:
    """Tests for _combine_adjacent_user_messages function."""

    def test_no_adjacent_users(self):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "Bye"},
        ]
        result, combined_any = _combine_adjacent_user_messages(messages)
        assert result == messages
        assert combined_any is False

    def test_adjacent_users_combined(self):
        messages = [
            {"role": "user", "content": "A"},
            {"role": "user", "content": "B"},
        ]
        result, combined_any = _combine_adjacent_user_messages(messages)
        assert len(result) == 1
        assert combined_any is True
        content = json.loads(result[0]["content"])
        assert content["content"] == [
            {"type": "text", "text": "A"},
            {"type": "text", "text": "B"},
        ]

    def test_multiple_groups_combined(self):
        messages = [
            {"role": "user", "content": "A"},
            {"role": "user", "content": "B"},
            {"role": "assistant", "content": "response"},
            {"role": "user", "content": "C"},
            {"role": "user", "content": "D"},
        ]
        result, combined_any = _combine_adjacent_user_messages(messages)
        assert len(result) == 3
        assert combined_any is True
        assert json.loads(result[0]["content"])["content"] == [
            {"type": "text", "text": "A"},
            {"type": "text", "text": "B"},
        ]
        assert result[1] == {"role": "assistant", "content": "response"}
        assert json.loads(result[2]["content"])["content"] == [
            {"type": "text", "text": "C"},
            {"type": "text", "text": "D"},
        ]

    def test_single_user_not_combined(self):
        messages = [{"role": "user", "content": "alone"}]
        result, combined_any = _combine_adjacent_user_messages(messages)
        assert result == messages
        assert combined_any is False

    def test_empty_list(self):
        result, combined_any = _combine_adjacent_user_messages([])
        assert result == []
        assert combined_any is False


class TestApplyProviderPreprocessing:
    """Tests for the main entry point."""

    def test_anthropic_full_preprocessing(self):
        kw = {
            "messages": [
                {"role": "user", "content": "A"},
                {"role": "system", "content": "sys"},
                {"role": "user", "content": "B"},
            ],
        }
        apply_provider_preprocessing(kw, "anthropic")

        # System moved to front, explanation added, users combined
        assert len(kw["messages"]) == 3
        assert kw["messages"][0] == {"role": "system", "content": "sys"}
        assert kw["messages"][1]["content"] == CONCURRENT_USER_MESSAGES_EXPLANATION
        assert json.loads(kw["messages"][2]["content"])["content"] == [
            {"type": "text", "text": "A"},
            {"type": "text", "text": "B"},
        ]

    def test_no_explanation_when_no_combining(self):
        kw = {
            "messages": [
                {"role": "system", "content": "sys"},
                {"role": "user", "content": "Hello"},
            ],
        }
        apply_provider_preprocessing(kw, "anthropic")

        assert len(kw["messages"]) == 2
        assert kw["messages"][0] == {"role": "system", "content": "sys"}
        assert kw["messages"][1] == {"role": "user", "content": "Hello"}

    def test_does_not_modify_original_messages(self):
        original = [
            {"role": "user", "content": "A"},
            {"role": "system", "content": "sys"},
        ]
        kw = {"messages": original}
        apply_provider_preprocessing(kw, "anthropic")

        # Original list reference unchanged, kw has new list
        assert original[0] == {"role": "user", "content": "A"}
        assert kw["messages"] is not original

    def test_non_anthropic_unchanged(self):
        kw = {
            "messages": [
                {"role": "user", "content": "A"},
                {"role": "system", "content": "sys"},
            ],
        }
        original_messages = kw["messages"]
        apply_provider_preprocessing(kw, "openai")

        assert kw["messages"] is original_messages

    def test_anthropic_fallback_chain(self):
        kw = {
            "messages": [
                {"role": "user", "content": "A"},
                {"role": "system", "content": "sys"},
            ],
        }
        apply_provider_preprocessing(kw, "anthropic->openai")
        assert kw["messages"][0] == {"role": "system", "content": "sys"}

    def test_non_anthropic_first_in_fallback(self):
        kw = {
            "messages": [
                {"role": "user", "content": "A"},
                {"role": "system", "content": "sys"},
            ],
        }
        original_messages = kw["messages"]
        apply_provider_preprocessing(kw, "openai->anthropic")
        assert kw["messages"] is original_messages

    def test_empty_messages(self):
        kw = {"messages": []}
        apply_provider_preprocessing(kw, "anthropic")
        assert kw["messages"] == []

    def test_missing_messages(self):
        kw = {"model": "test"}
        apply_provider_preprocessing(kw, "anthropic")
        assert "messages" not in kw

    def test_none_provider(self):
        kw = {"messages": [{"role": "user", "content": "A"}]}
        original = kw["messages"]
        apply_provider_preprocessing(kw, None)
        assert kw["messages"] is original


class TestEdgeCases:
    """Edge cases for the full preprocessing pipeline."""

    def test_all_system_messages(self):
        kw = {
            "messages": [
                {"role": "system", "content": "sys1"},
                {"role": "system", "content": "sys2"},
            ],
        }
        apply_provider_preprocessing(kw, "anthropic")
        # No combining, no explanation
        assert len(kw["messages"]) == 2

    def test_all_user_messages_combined(self):
        kw = {
            "messages": [
                {"role": "user", "content": "A"},
                {"role": "user", "content": "B"},
                {"role": "user", "content": "C"},
            ],
        }
        apply_provider_preprocessing(kw, "anthropic")
        # Explanation + combined user
        assert len(kw["messages"]) == 2
        assert kw["messages"][0]["content"] == CONCURRENT_USER_MESSAGES_EXPLANATION
        content = json.loads(kw["messages"][1]["content"])
        assert len(content["content"]) == 3

    def test_alternating_user_assistant_unchanged(self):
        messages = [
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
            {"role": "user", "content": "Q2"},
            {"role": "assistant", "content": "A2"},
        ]
        kw = {"messages": messages}
        apply_provider_preprocessing(kw, "anthropic")
        # No adjacent users, no changes (except deep copy)
        assert kw["messages"] == messages
