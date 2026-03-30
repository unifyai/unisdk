# Contributing to Unify

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

1. Clone the repository and install dependencies:

```bash
git clone https://github.com/unifyai/unify.git
cd unify
pip install uv
uv sync --group dev
```

2. Copy the environment template and fill in your API key:

```bash
cp .env.example .env
```

3. Install pre-commit hooks:

```bash
uv run pre-commit install
```

## Running Tests

Tests run against a live Orchestra instance. Set `UNIFY_KEY` and optionally `ORCHESTRA_URL` in your `.env`, then:

```bash
uv run pytest tests/path/to/test.py -v
```

## Code Style

This project uses automated formatting via pre-commit hooks:

- **Black** for code formatting
- **isort** for import sorting
- **autoflake** for removing unused imports

Hooks run automatically on `git commit`. If a commit fails because the hooks reformatted files, stage the changes and commit again.

You can also run the checks manually:

```bash
uv run pre-commit run --all-files
```

## CI

- The **black** formatting check runs on every push and works for all contributors.
- The full **pytest** suite requires org-level secrets (Orchestra access, GCP credentials) and runs only for maintainers. When a maintainer needs to trigger tests, include `[run-tests]` in the commit message or PR title.

## Pull Requests

- Open PRs against the `staging` branch.
- Keep changes focused -- one logical change per PR.
- Ensure `uv run pre-commit run --all-files` passes before submitting.
