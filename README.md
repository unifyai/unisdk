# Unify

Thin Python SDK wrapping the [Orchestra](https://github.com/unifyai/orchestra) REST API. Provides functional utilities for logging, project management, and assistant operations.

This package is used as a dependency by higher-level frameworks like [Unity](https://github.com/unifyai/unity).

## Installation

```bash
pip install unifyai
```

Or add to your project's dependencies pointing to this repo.

## Configuration

Set your API key via environment variable:

```bash
export UNIFY_KEY=<your-api-key>
```

Optionally override the API base URL (defaults to `https://api.unify.ai/v0`):

```bash
export UNIFY_BASE_URL=https://api.unify.ai/v0
```

## Core API

### Projects

```python
import unify

# Activate a project (creates if doesn't exist)
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

# Log entries
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

## Project Structure

```
unify/
├── __init__.py           # Public API exports
├── assistants/           # Assistant management
│   └── management.py
├── logging/              # Logging functionality
│   ├── logs.py          # Core Log class
│   └── utils/           # Logging utilities
│       ├── contexts.py  # Context management
│       ├── logs.py      # Log CRUD operations
│       └── projects.py  # Project CRUD operations
├── platform/             # Platform API
│   ├── queries.py       # Query logging
│   └── user.py          # User info
└── utils/                # Shared utilities
    ├── http.py          # HTTP client
    ├── storage.py       # Object storage
    ├── map.py           # Parallel mapping
    └── helpers.py       # Misc helpers
```

## Local Development

This project uses [Poetry](https://python-poetry.org/) for dependency management.

### Setup

```bash
poetry install
```

### Running Tests

```bash
poetry run pytest tests/path/to/test.py -v
```

If you encounter `Project _ not found` errors during test startup, unset the `CI` variable:

```bash
CI= poetry run pytest tests/path/to/test.py -v
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit` (Black, isort, autoflake). If a commit fails due to auto-formatting, re-run the commit.
