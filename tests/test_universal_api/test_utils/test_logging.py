from datetime import datetime, timedelta, timezone

import pytest

import unify

start_time = datetime.now(timezone.utc)
tag = "test_tag"
data = {
    "endpoint": "local_model_test@external",
    "query_body": {
        "messages": [
            {"role": "system", "content": "You are an useful assistant"},
            {"role": "user", "content": "Explain who Newton was."},
        ],
        "model": "llama-3-8b-chat@aws-bedrock",
        "max_tokens": 100,
        "temperature": 0.5,
    },
    "response_body": {
        "model": "meta.llama3-8b-instruct-v1:0",
        "created": 1725396241,
        "id": "chatcmpl-92d3b36e-7b64-4ae8-8102-9b7e3f5dd30f",
        "object": "chat.completion",
        "usage": {
            "completion_tokens": 100,
            "prompt_tokens": 44,
            "total_tokens": 144,
        },
        "choices": [
            {
                "finish_reason": "stop",
                "index": 0,
                "message": {
                    "content": "Sir Isaac Newton was an English mathematician, "
                    "physicist, and astronomer who lived from 1643 "
                    "to 1727.\\n\\nHe is widely recognized as one "
                    "of the most influential scientists in history, "
                    "and his work laid the foundation for the "
                    "Scientific Revolution of the 17th century."
                    "\\n\\nNewton's most famous achievement is his "
                    "theory of universal gravitation, which he "
                    "presented in his groundbreaking book "
                    '"Philosophi\\u00e6 Naturalis Principia '
                    'Mathematica" in 1687.',
                    "role": "assistant",
                },
            },
        ],
    },
    "timestamp": (start_time + timedelta(seconds=0.01)),
    "tags": [tag],
}


def test_log_query_manually():
    result = unify.log_query(**data)
    assert isinstance(result, dict)
    assert "info" in result
    assert result["info"] == "Query logged successfully"


def test_log_query_via_chat_completion():
    client = unify.Unify("gpt-4o@openai")
    response = client.generate(
        "hello",
        log_query_body=True,
        log_response_body=True,
    )
    assert isinstance(response, str)


def test_get_queries_from_manual():
    unify.log_query(**data)
    history = unify.get_queries(
        endpoints="local_model_test@external",
        start_time=start_time,
    )
    assert len(history) == 1
    history = unify.get_queries(
        endpoints="local_model_test@external",
        start_time=datetime.now(timezone.utc) + timedelta(seconds=1),
    )
    assert len(history) == 0


def test_get_queries_from_chat_completion():
    unify.Unify("gpt-4o@openai").generate(
        "hello",
        log_query_body=True,
        log_response_body=True,
    )
    history = unify.get_queries(
        endpoints="gpt-4o@openai",
        start_time=start_time,
    )
    assert len(history) == 1
    history = unify.get_queries(
        endpoints="gpt-4o@openai",
        start_time=datetime.now(timezone.utc) + timedelta(seconds=1),
    )
    assert len(history) == 0


def test_get_query_failures():
    client = unify.Unify("gpt-4o@openai")
    client.generate(
        "hello",
        log_query_body=True,
        log_response_body=True,
    )
    with pytest.raises(Exception):
        client.generate(
            "hello",
            log_query_body=True,
            log_response_body=True,
            drop_params=False,
            invalid_arg="invalid_value",
        )

    # inside logged timeframe
    history_w_both = unify.get_queries(
        endpoints="gpt-4o@openai",
        start_time=start_time,
        failures=True,
    )
    assert len(history_w_both) == 2
    history_only_failures = unify.get_queries(
        endpoints="gpt-4o@openai",
        start_time=start_time,
        failures="only",
    )
    assert len(history_only_failures) == 1
    history_only_success = unify.get_queries(
        endpoints="gpt-4o@openai",
        start_time=start_time,
        failures=False,
    )
    assert len(history_only_success) == 1

    # Outside logged timeframe
    history_w_both = unify.get_queries(
        endpoints="gpt-4o@openai",
        start_time=datetime.now(timezone.utc) + timedelta(seconds=1),
        failures=True,
    )
    assert len(history_w_both) == 0
    history_only_failures = unify.get_queries(
        endpoints="gpt-4o@openai",
        start_time=datetime.now(timezone.utc) + timedelta(seconds=1),
        failures="only",
    )
    assert len(history_only_failures) == 0
    history_only_success = unify.get_queries(
        endpoints="gpt-4o@openai",
        start_time=datetime.now(timezone.utc) + timedelta(seconds=1),
        failures=False,
    )
    assert len(history_only_success) == 0


def test_get_query_tags():
    unify.log_query(**data)
    tags = unify.get_query_tags()
    assert isinstance(tags, list)
    assert tag in tags


if __name__ == "__main__":
    pass
