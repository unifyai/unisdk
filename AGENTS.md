<!--
    GENERATED FILE - DO NOT EDIT DIRECTLY.

    Regenerate with:  python3 .agents/global-rules/build_agents_md.py

    Edit the sources instead:
      .agents/repo.md              this repo's overview and always-on guidance
      .agents/rules/*.md           this repo's own rules
      .agents/shared.txt           which shared rules this repo includes
      .agents/global-rules/rules/  rules shared across all unifyai repos
                                   (submodule: unifyai/global-agent-rules)
-->

# UniSDK: The Python SDK for Orchestra

UniSDK is a thin Python SDK that wraps Orchestra's REST API, providing a clean programmatic interface for projects, logging, contexts, and storage operations.

## Core Functionality

- **Projects**: `create_project()`, `list_projects()`, `delete_project()`, `activate()`
- **Logging**: `log()`, `get_logs()`, `create_fields()`, `delete_logs()`
- **Contexts**: `create_context()`, `get_context()`, `commit_context()`, `rollback_context()`
- **Storage**: `get_signed_url()`, `download_object()`
- **Utilities**: `map()` for parallel operations with automatic logging

## Design Philosophy

The SDK abstracts away HTTP communication, handles authentication via `UNIFY_KEY`, and provides a Pythonic interface. This creates clean separation: consuming code (like Unify) focuses on business logic while UniSDK handles API communication.

## Position in the System

UniSDK sits between Unify and Orchestra. When Unify's managers need to persist data, they call UniSDK functions rather than making raw HTTP calls. This indirection allows Orchestra's API to evolve independently of its consumers, with UniSDK providing a stable interface.

## Related Repositories

- **orchestra**: The backend API that UniSDK wraps
- **unify**: Primary consumer of UniSDK for all persistence operations
- **unillm**: Independent (parallel SDK, not dependent on UniSDK)
- **unify-deploy**: Hosted communication stack may use UniSDK for logging/storage operations
- **console**: Uses Orchestra API directly (TypeScript), not the Python SDK

---

# Repository rules

# Local Development Environment

## Package Manager

This project uses **uv** for dependency management. Do not use pip, poetry, or other package managers.

## Python Interpreter

- Use `uv run` to execute commands within the virtual environment.
- uv creates a local `.venv` directory in the project root.
- To check the environment: `uv venv --python 3.12` (if needed)

## Environment Bootstrap

If the environment is not set up, install dependencies with:

```bash
uv sync --group dev
```

## Running Tests

### Default Contributor Check

```bash
uv run pre-commit run --all-files
```

### Mocked Smoke Tests

These tests do not require the internal Orchestra/GCP stack:

```bash
uv run pytest tests/test_async_admin.py tests/test_storage.py tests/test_http.py -v
```

### Full Integration Suite

Most of the test suite exercises a live backend or a local Orchestra deployment.
Set `UNIFY_KEY` and optionally `ORCHESTRA_URL` in `.env`, then run the target
pytest path directly.

```bash
# Single test file
uv run pytest tests/test_contexts.py -v

# Specific test function
uv run pytest tests/test_projects.py::test_create_project -v

# Multiple specific tests
uv run pytest tests/test_async_admin.py tests/test_storage.py -v

# Entire directory
uv run pytest tests/ -v
```

## Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`. They include:
- Black (formatting)
- isort (import sorting)
- autoflake (unused import removal)
- YAML/TOML/whitespace hygiene checks

If a commit fails due to auto-formatting, simply re-run the commit command - the hooks will have fixed the files.

## Dependencies

- Config file: `pyproject.toml`
- Lock file: `uv.lock`
- Do not edit `uv.lock` manually. Use `uv add`, `uv remove`, or `uv sync`.
