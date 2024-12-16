# Unify

<a href="https://www.ycombinator.com/companies/unify">![Static Badge](https://img.shields.io/badge/Y%20Combinator-W23-orange)</a>
<a href="https://x.com/letsunifyai">![X (formerly Twitter) Follow](https://img.shields.io/twitter/follow/letsunifyai)</a>
<a href="https://discord.gg/sXyFF8tDtm"> ![Static Badge](https://img.shields.io/badge/Join_Discord-464646?&logo=discord&logoColor=5865F2) </a>

Unify is a fully **hackable LLMOps platform**, which you can use to build *personalized* pipelines for: logging, evaluations, guardrails, human labelling, agentic workflows, self-optimization, and more.

simply `unify.log` your data, and then compose your own custom interface using the four core building blocks: (1) **tables**, (2) **plots**, (3) **visualizations**, and (4) **terminals**.

Despite the explosion of LLM tools, many of these are inflexible, overly abstracted, and complex to navigate.

Tooling requirements constantly change across *projects*, across *teams*, and across *time*. We've therefore made Unify as simple, modular and hackable as possible, so you can spin up and iterate on the *exact* AI platform that **you** need, in **seconds** ⚡

## Why LLMOps?

**Software 1.0:** Human-written source code, deterministic unit tests, etc. 🧑‍💻

**Software 2.0:** Neural networks, validation losses, etc. 📉

**Software 3.0:** LLMs?

LLMs are *a bit* like **Software 1.0**, with human interpretable "code" (natural language) and with often symbolic unit tests, but they are also *a bit* like **Software 2.0**, with non-determinism, hyperparameters, and black-box logic under the hood.

Building an effective LLMOps pipeline requires taking **both of these perspectives** into account, mixing aspects of both **DevOps and MLOps** 🌀

## LLM Flywheel

Despite all of the recent hype, the overly complex abstractions, and the jargon, the *process* for building high-performing LLM application is **remarkably simple**. In pseudo-code:

```
While True:
    Update unit tests (evals) 🗂️
    while run(tests) failing: 🧪
        Vary system prompt, in-context examples, available tools etc. 🔁
    Beta test with users, find more failures from production traffic 🚦
```

## Quickstart

[Sign up](https://console.unify.ai/), `pip install unifyai`, and make your first LLM query:

```python
import unify
client = unify.Unify("gpt-4o@openai", api_key="UNIFY_KEY")
client.generate("hello world!")
```

> [!NOTE]
> We recommend using [python-dotenv](https://pypi.org/project/python-dotenv/)
> to add `UNIFY_KEY="My API Key"` to your `.env` file, avoiding the need to use the `api_key` argument as above.

You can list all available LLM endpoints, models and providers like so:

```python
unify.list_models()
unify.list_providers()
unify.list_endpoints()
```

Now you can run this toy evaluation ⬇️, check out the logs in your [dashboard](https://console.unify.ai/evals), and iterate 🔁 on your parameters to quickly get your application flying! 🪁

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

A *complete* example of this Maths Assistant problem can be found [here](https://docs.unify.ai/data_flywheel/teaching_assistant).

## Learn More

Check out our [docs](https://docs.unify.ai/) (especially our [Walkthrough](https://docs.unify.ai/basics/welcome)) to get through the major concepts quickly. If you have any questions, feel free to reach out to us on [discord](https://discord.com/invite/sXyFF8tDtm) 👾

Happy prompting! 🧑‍💻
