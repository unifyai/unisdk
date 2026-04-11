# Unify

Python SDK for the persistence and state layer behind [Unity](https://github.com/unifyai/unity). It wraps the backend REST API in a clean functional interface for projects, structured logging, contexts, storage, and assistant management.

If you're here from the Unity quickstart, this is the layer behind `UNIFY_KEY`: Unity runs locally, while `unify` connects the managers to the backend that stores project state, logs, and other persistent data.

## What layer is this?

Unify is the persistence plane used by Unity's managers. When Unity needs to store contacts, log conversations, query knowledge, or manage projects, it calls `unify`. When you want to interact with the same data programmatically — inspect logs, manage projects, upload files, or query assistant state — you use this SDK directly.

In the default open-source Unity flow, the layering looks like this:

| Layer | Repo | Role |
|------|------|------|
| Runtime / orchestration | [unity](https://github.com/unifyai/unity) | Runs the agent brain locally |
| Persistence / state | **unify** (this repo) | Connects the runtime to backend state and logging |
| Model access | [unillm](https://github.com/unifyai/unillm) | Routes LLM calls to the provider or endpoint the developer chooses |

## Installation

```bash
pip install git+https://github.com/unifyai/unify.git
```

## Configuration

Set your API key for the default hosted backend:

```bash
export UNIFY_KEY=<your-api-key>
```

Optionally override the backend API base URL (defaults to `https://api.unify.ai/v0`):

```bash
export ORCHESTRA_URL=https://api.unify.ai/v0
```

## Usage

### Projects

```python
import unify

# Activate a project (creates if it doesn't exist)
unify.activate("my-project")

# Or manage projects directly
unify.create_project("my-project")
unify.list_projects()
unify.delete_project("my-project")
```

### Logging

```python
import unify

unify.activate("my-project")

# Log entries with arbitrary fields
unify.log(question="What is 2+2?", response="4", score=1.0)

# Retrieve logs
logs = unify.get_logs()
```

### Parallel Mapping

```python
import unify

def process(item):
    # ... do work ...
    unify.log(item=item, result=result)

unify.map(process, items)
```

## Backend configuration

By default, `unify` targets Unify's hosted API. If you're running against a different deployment, point `ORCHESTRA_URL` at that base URL and keep using the same SDK surface.

See the [Unity README](https://github.com/unifyai/unity) for the broader architecture and the default quickstart that uses this SDK.

## Project structure

```
unify/
├── __init__.py           # Public API exports
├── agent.py              # Agent messaging (send/receive)
├── assistants.py         # Assistant listing
├── async_admin.py        # Async spend tracking client
├── _async_logger.py      # Async log manager
├── contexts.py           # Context CRUD operations
├── logs.py               # Core Log class and log operations
├── platform.py           # Platform API (credits, user info)
├── projects.py           # Project CRUD operations
└── utils/
    ├── helpers.py         # Misc helpers
    ├── http.py            # HTTP client
    ├── map.py             # Parallel mapping
    └── storage.py         # Object storage (signed URLs)
```

## Local development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

### Setup

```bash
pip install uv
uv sync --group dev
cp .env.example .env
```

### Running tests

Tests run against a live backend instance:

```bash
uv run pytest tests/path/to/test.py -v
```

### CI

The `black` formatting check runs on every push and works for all contributors. The full test suite requires org-level secrets and runs only for maintainers — see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Pre-commit hooks

Pre-commit hooks run automatically on `git commit` (Black, isort, autoflake). If a commit fails due to auto-formatting, re-run the commit.

## License

MIT — see [LICENSE](LICENSE) for details.

Built by the team at [Unify](https://unify.ai).
