# Unify

Python SDK for the [Unify](https://unify.ai) platform backend. Wraps the REST API in a clean functional interface for projects, structured logging, contexts, storage, and assistant management.

## What is Unify?

Unify builds AI assistants with their own computer, memory, and communication channels. The assistants communicate via phone, SMS, and email, manage tasks, retain knowledge across conversations, and operate continuously. The platform is a distributed system of specialized managers orchestrated by [Unity](https://github.com/unifyai/unity), the brain.

This SDK is the persistence layer. When Unity's managers need to store contacts, log conversations, query knowledge, or manage projects, they call Unify. When you want to interact with the same data programmatically — inspect logs, manage projects, upload files — you use Unify directly.

## Installation

```bash
pip install git+https://github.com/unifyai/unify.git
```

## Configuration

Set your API key:

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

## How it fits together

Unify is one piece of a larger open-source system:

| Repo | What it does |
|------|-------------|
| **[unity](https://github.com/unifyai/unity)** | The brain — managers, tool loops, orchestration |
| **unify** (this) | Python SDK for the backend API |
| **[unillm](https://github.com/unifyai/unillm)** | LLM abstraction — caching, tracing, cost tracking |

See the [Unity README](https://github.com/unifyai/unity) for the full architecture.

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

Apache 2.0

Built by the team at [Unify](https://unify.ai).
