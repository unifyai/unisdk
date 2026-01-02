
<a href="https://console.unify.ai/">
    <picture>
        <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/unifyai/unifyai.github.io/refs/heads/main/img/logos/unify_logo_inverted_cropped.svg"/>
        <img class="dark-light" width="30%" src="https://raw.githubusercontent.com/unifyai/unifyai.github.io/refs/heads/main/img/logos/unify_logo_cropped.svg"/>
    </picture>
</a>

----

<a href="https://www.ycombinator.com/companies/unify">![Static Badge](https://img.shields.io/badge/Y%20Combinator-W23-orange)</a>
<a href="https://x.com/letsunifyai">![X (formerly Twitter) Follow](https://img.shields.io/twitter/follow/letsunifyai)</a>
<a href="https://discord.gg/sXyFF8tDtm"> ![Static Badge](https://img.shields.io/badge/Join_Discord-464646?&logo=discord&logoColor=5865F2) </a>

<div style="display: block;" align="center">
    <a href="https://console.unify.ai/">
        <img class="dark-light" width="100%" src="https://raw.githubusercontent.com/unifyai/unifyai.github.io/refs/heads/main/img/externally_linked/docs/line_group_dark.gif"/>
    </a>
</div>

**Fully hackable** LLMOps. Build *custom* interfaces for: logging, evals, guardrails, labelling, agents, human-in-the-loop, hyperparam sweeps, and anything else you can think of ✨

Just `unify.log` your data, and add an interface using the four building blocks:

1.  **tables** 🔢
2.  **views** 🔍
3. **plots** 📊
4. **editor** 🕹️ (coming soon)

Every LLM product has **unique** and **changing** requirements, as do the **users**. Your infra should reflect this!

We've tried to make Unify as **(a) simple**, **(b) modular** and **(c) hackable** as possible, so you can quickly probe, analyze, and iterate on the data that's important for **you**, your **product** and your **users** ⚡

## Quickstart

[Sign up](https://console.unify.ai/), `pip install unifyai`, run your first eval ⬇️, and then check out the logs in your first [interface](https://console.unify.ai) 📊

```python
import unify
import litellm
from random import randint, choice

# initialize project
unify.activate("Maths Assistant")

SYSTEM_MESSAGE = (
    "You are a helpful maths assistant, "
    "tasked with adding and subtracting integers."
)

# add test cases
qs = [
    f"{randint(0, 100)} {choice(['+', '-'])} {randint(0, 100)}"
    for i in range(10)
]

# define evaluator
def evaluate_response(question: str, response: str) -> float:
    correct_answer = eval(question)
    try:
        response_int = int(
            "".join(
                [
                    c for c in response.split(" ")[-1]
                    if c.isdigit()
                ]
            ),
        )
        return float(correct_answer == response_int)
    except ValueError:
        return 0.

# define evaluation
def evaluate(q: str):
    response = litellm.completion(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": q},
        ],
    )
    response_text = response.choices[0].message.content
    score = evaluate_response(q, response_text)
    unify.log(
        question=q,
        response=response_text,
        score=score
    )

# execute + log your evaluation
with unify.Experiment():
    unify.map(evaluate, qs)
```

Check out our [Quickstart Video](https://youtu.be/fl9SzsoCegw?si=MhQZDfNS6U-ZsVYc) for a guided walkthrough.

## Focus on your *product*, not the *LLM* 🎯

Despite all of the hype, abstractions, and jargon, the *process* for building quality LLM apps is pretty simple.

```
create simplest possible agent 🤖
while True:
    create/expand unit tests (evals) 🗂️
    while run(tests) failing: 🧪
        Analyze failures, understand the root cause 🔍
        Vary system prompt, in-context examples, tools etc. to rectify 🔀
    Beta test with users, find more failures 🚦
```

We've tried to strip away all of the excessive LLM jargon, so you can focus on your *product*, your *users*, and the *data* you care about, and *nothing else* 📈

Unify takes inspiration from:
- [PostHog](https://posthog.com/) / [Grafana](https://grafana.com/) / [LogFire](https://pydantic.dev/logfire) for powerful observability 🔬
- [LangSmith](https://www.langchain.com/langsmith) / [BrainTrust](https://www.braintrust.dev/) / [Weave](https://wandb.ai/site/weave/) for LLM abstractions 🤖
- [Notion](https://www.notion.com/) / [Airtable](https://www.airtable.com/) for composability and versatility 🧱

Whether you're technical or non-technical, we hope Unify can help you to rapidly build top-notch LLM apps, and to remain fully focused on your *product* (not the *LLM*).

## Contributing

This project uses [Poetry](https://python-poetry.org/) for dependency management. To set up a development environment:

```bash
poetry install
```

To run tests:

```bash
poetry run pytest tests/path/to/test.py -v
```

## Learn More

Check out our [docs](https://docs.unify.ai/), and if you have any questions feel free to reach out to us on [discord](https://discord.com/invite/sXyFF8tDtm) 👾

Unify is under active development 🚧, feedback in all shapes/sizes is also very welcome! 🙏

Happy prompting! 🧑‍💻
