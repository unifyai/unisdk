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
