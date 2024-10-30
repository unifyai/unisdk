import os
import unify

dir_path = os.path.dirname(os.path.realpath(__file__))


def _assert_prompt_msg(prompt, user_msg):
    assert "messages" in prompt.__dict__
    assert isinstance(prompt.messages, list)
    assert len(prompt.messages) > 0
    assert "content" in prompt.messages[0]
    assert prompt.messages[0]["content"] == user_msg


def _assert_prompt_param(prompt, param_name, param_val):
    assert param_name in prompt.__dict__
    assert prompt.__dict__[param_name] == param_val


def test_create_prompt_from_user_message() -> None:
    prompt = unify.Prompt("Hello")
    _assert_prompt_msg(prompt, "Hello")


def test_create_prompt_from_messages() -> None:
    prompt = unify.Prompt(messages=[{"role": "user", "content": "Hello"}])
    _assert_prompt_msg(prompt, "Hello")


def test_create_prompt_from_messages_n_params() -> None:
    prompt = unify.Prompt(
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.5,
    )
    _assert_prompt_msg(prompt, "Hello")
    _assert_prompt_param(prompt, "temperature", 0.5)


def test_pass_prompts_to_client() -> None:
    prompt = unify.Prompt(
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.5,
    )
    client = unify.Unify(**prompt.model_dump(), cache=True)
    assert client.temperature == 0.5


if __name__ == "__main__":
    pass
