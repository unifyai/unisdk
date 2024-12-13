# Unify

<div style="display: block;" align="center">
    <img class="dark-light" width="100%" src="https://github.com/unifyai/unifyai.github.io/blob/main/img/externally_linked/github_header.gif?raw=true"/>
</div>

**Software 1.0:** Human-written source code, deterministic unit tests, etc. 🧑‍💻

**Software 2.0:** Neural networks, validation losses, etc. 📉

**Software 3.0:** LLMs?

LLMs are *a bit* like **Software 1.0**, with human interpretable "code" (natural language) and with often symbolic unit tests, but they are also *a bit* like **Software 2.0**, with non-determinism, hyperparameters, and black-box logic under the hood.

Building an effective LLMOps pipeline requires taking **both of these perspectives** into account, mixing aspects of both **DevOps and MLOps** 🌀

## LLM Flywheel

Despite all of the recent hype, the overly complex abstractions, and the jargon, building LLM application is **remarkably simple**. In pseudo-code:

```
While True:
    Update unit tests (evals) 🗂️
    while run(tests) failing: 🧪
        Vary system prompt, in-context examples, available tools etc. 🔁
    Beta test with users, find more failures from production traffic 🚦
```

## Quickstart

[Sign up](https://console.unify.ai/), `pip install unifyai`, run this toy evaluation ⬇️, check out the logs in your [dashboard](https://console.unify.ai/evals), and then iterate 🔁 on your parameters to quickly get your application flying! 🪁

```python
import unify
from random import randint, choice

# agent
client = unify.Unify("gpt-4o@openai")
client.set_system_message("You are a helpful maths assistant, tasked with adding and subtracting integers.")

# test cases
qs = [f"{randint(0, 100)} {choice(['+', '-'])} {randint(0, 100)}" for i in range(10)]

# evaluator
def evaluate_response(question: str, response: str) -> float:
    correct_answer = eval(question)
    try:
        response_int = int(
            "".join([c for c in response.split(" ")[-1] if c.isdigit()]),
        )
        return float(correct_answer == response_int)
    except ValueError:
        return 0.

# evaluation
def evaluate(q: str):
    response = client.generate(q)
    score = evaluate_response(q, response)
    unify.log(
        question=q,
        response=response,
        score=score
    )

# execute + log evaluation
with unify.Project("Maths Assistant"):
    with unify.Params(system_message=client.system_message):
        unify.map(evaluate, qs)
```

<div style="display: block;" align="center">
    <img class="dark-light" width="100%" src="https://media.githubusercontent.com/media/unifyai/unifyai.github.io/refs/heads/main/img/externally_linked/evals_console.gif"/>
</div>

A *complete* example of this Maths Assistant problem can be found here.

## Learn More

Check out our docs (especially our walkthrough) to get through the major concepts quickly. Happy prompting! 🧑‍💻
