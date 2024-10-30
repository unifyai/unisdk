import json

from unify import Unify


def test_openai_json_mode() -> None:
    client = Unify(endpoint="gpt-4o@openai")
    result = client.generate(
        system_message="You are a helpful assistant designed to output JSON.",
        user_message="Who won the world series in 2020?",
        response_format={"type": "json_object"},
    )
    assert isinstance(result, str)
    result = json.loads(result)
    assert isinstance(result, dict)


def test_anthropic_json_mode() -> None:
    client = Unify(endpoint="claude-3-opus@anthropic")
    result = client.generate(
        system_message="You are a helpful assistant designed to output JSON.",
        user_message="Who won the world series in 2020?",
    )
    assert isinstance(result, str)
    result = json.loads(result)
    assert isinstance(result, dict)


if __name__ == "__main__":
    pass
