import unify


def test_time_to_first_token():
    for pre in ("", "lowest-"):
        unify.Unify(f"claude-3-opus@{pre}time-to-first-token").generate("Hello.")
        unify.Unify(f"gpt-4o@{pre}ttft").generate("Hello.")
        unify.Unify(f"mixtral-8x22b-instruct-v0.1@{pre}t").generate("Hello.")


def test_inter_token_latency():
    for pre in ("", "lowest-"):
        unify.Unify(f"claude-3-opus@{pre}inter-token-latency").generate("Hello.")
        unify.Unify(f"gpt-4o@{pre}itl").generate("Hello.")
        unify.Unify(f"mixtral-8x22b-instruct-v0.1@{pre}i").generate("Hello.")


def test_cost():
    for pre in ("", "lowest-"):
        unify.Unify(f"claude-3-opus@{pre}cost").generate("Hello.")
        unify.Unify(f"mixtral-8x22b-instruct-v0.1@{pre}c").generate("Hello.")


def test_input_cost():
    for pre in ("", "lowest-"):
        unify.Unify(f"claude-3-opus@{pre}input-cost").generate("Hello.")
        unify.Unify(f"gpt-4o@{pre}ic").generate("Hello.")
        unify.Unify(f"mixtral-8x22b-instruct-v0.1@{pre}i").generate("Hello.")


def test_output_cost():
    for pre in ("", "lowest-"):
        unify.Unify(f"claude-3-opus@{pre}output-cost").generate("Hello.")
        unify.Unify(f"mixtral-8x22b-instruct-v0.1@{pre}oc").generate("Hello.")


if __name__ == "__main__":
    pass
