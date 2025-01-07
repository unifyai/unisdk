import unify


def test_provider_fallback():
    unify.Unify("claude-3-opus@anthropic->aws-bedrock").generate("Hello.")


def test_model_fallback():
    unify.Unify("gemini-1.5-pro->gemini-1.5-flash@vertex-ai").generate("Hello.")


def test_endpoint_fallback():
    unify.Unify(
        "llama-3.1-405b-chat@together-ai->gpt-4o@openai",
    ).generate("Hello.")


if __name__ == "__main__":
    pass
