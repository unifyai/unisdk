import unify


def test_inter_token_latency():
    unify.Unify("claude-3-opus@inter-token-latency").generate("Hello.")
    unify.Unify("gpt-4o@itl").generate("Hello.")
    unify.Unify("mixtral-8x22b-instruct-v0.1@i").generate("Hello.")
