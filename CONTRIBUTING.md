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

The `.cursor/` directory and the `global-cursor-rules` submodule are optional editor tooling. They are not required for normal development.

## Running Tests

### Default contributor check

Public PRs are expected to pass the pre-commit suite:

```bash
uv run pre-commit run --all-files
```

### Optional local smoke tests

These mocked tests do not require the internal Orchestra/GCP stack:

```bash
uv run pytest tests/test_async_admin.py tests/test_storage.py tests/test_http.py -v
```

### Full integration suite

Most of the test suite runs against a live backend or a local Orchestra deployment. Set `UNIFY_KEY` and optionally `ORCHESTRA_URL` in your `.env`, then:

```bash
uv run pytest tests/path/to/test.py -v
```

## Code Style

This project uses automated formatting via pre-commit hooks:

- **Black** for code formatting
- **isort** for import sorting
- **autoflake** for removing unused imports
- Basic TOML, YAML, and whitespace hygiene checks

Hooks run automatically on `git commit`. If a commit fails because the hooks reformatted files, stage the changes and commit again.

You can also run the checks manually:

```bash
uv run pre-commit run --all-files
```

## CI

- External PRs and forks run the pre-commit lint/format checks only.
- The full **pytest** suite requires org-level secrets (backend access, GCP credentials) and internal infrastructure, so it runs only on maintainer-controlled branches and via manual workflow dispatch.

## Pull Requests

- Open PRs against the `staging` branch.
- Keep changes focused -- one logical change per PR.
- Ensure `uv run pre-commit run --all-files` passes before submitting.
