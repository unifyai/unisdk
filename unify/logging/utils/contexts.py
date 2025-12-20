from typing import Any, Dict, List, Optional, Union

from unify import BASE_URL
from unify.utils import http
from unify.utils.http import RequestError

from ...utils.helpers import _create_request_header, _get_and_maybe_create_project
from .logs import CONTEXT_WRITE

# Contexts #
# ---------#


def create_context(
    name: str,
    description: str = None,
    is_versioned: bool = True,
    allow_duplicates: bool = True,
    unique_keys: Optional[Dict[str, str]] = None,
    auto_counting: Optional[Dict[str, Optional[str]]] = None,
    foreign_keys: Optional[List[Dict[str, Any]]] = None,
    exist_ok: bool = True,
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> None:
    """
    Create a context.

    Args:
        name: Name of the context to create.

        description: Description of the context to create.

        is_versioned: Whether the context is tracked via version control.

        allow_duplicates: Whether to allow duplicates in the context.

        unique_keys: Unique key definition. Keys are column names, values are types
            ('str', 'int', 'float', 'bool', 'datetime', 'time', 'date', 'timedelta', 'dict', 'list').
            Default is None.

        auto_counting: Auto-counting configuration. Keys are column names to auto-increment,
            values are parent counter names (None for independent counters). Default is None.

        foreign_keys: Foreign key definitions for referential integrity. Each foreign key is a
            dictionary with the following keys:
            - name (str): Column name or nested path that references another context.
              Supported path patterns:
              • Simple column: "department_id"
              • Flat array: "tag_ids[*]" - references all values in array of primitives
              • Nested array: "images[*].image_id" - references field in array of objects
              • Array element (specific): "items[0].id" - references specific index
              • Nested objects: "metadata.user.user_id" - deep object navigation
              • Mixed nesting: "teams[*].members[*].user_id" - multiple array levels
            - references (str): Referenced context and column in format "ContextName.column_name"
            - on_delete (str): Action to perform when referenced row is deleted.
                Supported actions: "CASCADE", "SET NULL"
            - on_update (str): Action to perform when referenced row is updated.
                Supported actions: "CASCADE", "SET NULL"
            Example: [{"name": "department_id", "references": "Departments.id",
                      "on_delete": "CASCADE", "on_update": "CASCADE"}]
            Default is None.

        exist_ok: If True (default), silently succeeds when the context already exists.
            If False, raises an error when the context already exists.

        project: Name of the project the context belongs to.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A message indicating whether the context was successfully created.

    Example:
        # Simple foreign key (direct column reference)
        create_context(
            name="Departments",
            unique_keys={"id": "int"},
            auto_counting={"id": None},
            project="my_project"
        )
        create_context(
            name="Employees",
            foreign_keys=[
                {
                    "name": "department_id",  # Simple column
                    "references": "Departments.id",
                    "on_delete": "CASCADE",
                    "on_update": "CASCADE"
                }
            ],
            project="my_project"
        )

        # Flat array FK - references array of primitive values
        create_context(
            name="Categories",
            unique_keys={"category_id": "int"},
            auto_counting={"category_id": None},
            project="my_project"
        )
        create_context(
            name="Products",
            foreign_keys=[
                {
                    "name": "category_ids[*]",  # All values in array of primitives
                    "references": "Categories.category_id",
                    "on_delete": "CASCADE",
                    "on_update": "CASCADE"
                }
            ],
            project="my_project"
        )

        # Nested array FK - references field in array of objects
        create_context(
            name="Images",
            unique_keys={"image_id": "int"},
            auto_counting={"image_id": None},
            project="my_project"
        )
        create_context(
            name="Transcripts",
            foreign_keys=[
                {
                    "name": "images[*].image_id",  # Field in array of objects
                    "references": "Images.image_id",
                    "on_delete": "CASCADE",
                    "on_update": "CASCADE"
                }
            ],
            project="my_project"
        )

        # Nested object FK - deep object path navigation
        create_context(
            name="Users",
            unique_keys={"user_id": "int"},
            auto_counting={"user_id": None},
            project="my_project"
        )
        create_context(
            name="Records",
            foreign_keys=[
                {
                    "name": "metadata.user.user_id",  # Nested through objects
                    "references": "Users.user_id",
                    "on_delete": "SET NULL",
                    "on_update": "CASCADE"
                }
            ],
            project="my_project"
        )

        # Mixed nesting - combining arrays and objects
        create_context(
            name="Projects",
            foreign_keys=[
                {
                    "name": "teams[*].members[*].user_id",  # Multiple array levels
                    "references": "Users.user_id",
                    "on_delete": "CASCADE",
                    "on_update": "CASCADE"
                }
            ],
            project="my_project"
        )
    """
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    headers = _create_request_header(api_key)
    body = {
        "name": name,
        "description": description,
        "is_versioned": is_versioned,
        "allow_duplicates": allow_duplicates,
        "unique_keys": unique_keys,
        "auto_counting": auto_counting,
        "foreign_keys": foreign_keys,
    }
    try:
        response = http.post(
            BASE_URL + f"/project/{project}/contexts",
            headers=headers,
            json=body,
        )
        return response.json()
    except RequestError as e:
        if (
            exist_ok
            and e.response.status_code == 400
            and "already exists" in e.response.text
        ):
            return None
        raise


def create_contexts(
    contexts: List[Union[Dict[str, Any], str]],
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> None:
    """
    Create multiple contexts.

    Args:
        contexts: List of contexts to create. Each context can be a list of context names or a dictionary with the following keys, only the name is required:
            - name: Name of the context.
            - description: Description of the context.
            - is_versioned: Whether the context is tracked via version control.
            - allow_duplicates: Whether to allow duplicates in the context.
            - unique_keys: Unique key definition. Keys are column names, values are types
                ('str', 'int', 'float', 'bool', 'datetime', 'time', 'date', 'timedelta', 'dict', 'list').
            - auto_counting: Auto-counting configuration. Keys are column names to auto-increment,
                values are parent counter names (None for independent counters).
            - foreign_keys: Foreign key definitions for referential integrity. List of dictionaries,
                each with keys: name (supports nested paths like "tag_ids[*]", "images[*].image_id", or "metadata.user.id"),
                references, on_delete, on_update. Supported actions: "CASCADE", "SET NULL".

        project: Name of the project the contexts belong to.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A message indicating whether the contexts were successfully created.

    Example:
        create_contexts(
            contexts=[
                {
                    "name": "Departments",
                    "unique_keys": {"id": "int"},
                    "auto_counting": {"id": None}
                },
                {
                    "name": "Employees",
                    "foreign_keys": [
                        {
                            "name": "department_id",
                            "references": "Departments.id",
                            "on_delete": "CASCADE",
                            "on_update": "CASCADE"
                        }
                    ]
                }
            ],
            project="my_project"
        )
    """
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    headers = _create_request_header(api_key)
    response = http.post(
        BASE_URL + f"/project/{project}/contexts",
        headers=headers,
        json=contexts,
    )
    return response.json()


def rename_context(
    name: str,
    new_name: str,
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> None:
    """
    Rename a context.

    Args:
        name: Name of the context to rename.

        new_name: New name of the context.

        project: Name of the project the context belongs to.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.
    """
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    headers = _create_request_header(api_key)
    response = http.patch(
        BASE_URL + f"/project/{project}/contexts/{name}/rename",
        headers=headers,
        json={"name": new_name},
    )
    return response.json()


def get_context(
    name: str,
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get information about a specific context including its versioning status and current version.

    Args:
        name: Name of the context to get.

        project: Name of the project the context belongs to.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing context information with the following keys:
            - name (str): Name of the context
            - description (str): Description of the context
            - is_versioned (bool): Whether the context is versioned
            - allow_duplicates (bool): Whether duplicates are allowed
            - unique_keys (list): List of unique key column names
            - auto_counting (dict): Auto-counting configuration
            - foreign_keys (list): List of foreign key definitions, each containing:
                - name: FK column name or nested path (e.g., "tag_ids[*]", "images[*].image_id", "metadata.user.id")
                - references: Referenced context and column
                - on_delete: Action on delete (CASCADE, SET NULL)
                - on_update: Action on update (CASCADE, SET NULL)
                - is_nested: Boolean indicating if this uses a nested path
                - path_segments: Parsed path structure (for nested FKs)

    Example:
        context_info = get_context(name="Employees", project="my_project")
        # Returns:
        # {
        #     "name": "Employees",
        #     "description": "Employee data",
        #     "is_versioned": False,
        #     "allow_duplicates": True,
        #     "unique_keys": [],
        #     "auto_counting": {},
        #     "foreign_keys": [
        #         {
        #             "name": "department_id",
        #             "references": "Departments.id",
        #             "on_delete": "CASCADE",
        #             "on_update": "CASCADE"
        #         }
        #     ]
        # }
    """
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    headers = _create_request_header(api_key)
    response = http.get(
        BASE_URL + f"/project/{project}/contexts/{name}",
        headers=headers,
    )
    return response.json()


def get_contexts(
    project: Optional[str] = None,
    *,
    prefix: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Gets all contexts associated with a project, with the corresponding prefix.

    Args:
        project: Name of the project the contexts belong to.

        prefix: Prefix of the contexts to get (optional filter).

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A dictionary mapping context names to their descriptions.

    Note:
        This function returns only context names and descriptions. To get full context
        details including foreign_keys, unique_keys, auto_counting, and other configuration,
        use get_context() for individual contexts.

    Example:
        contexts = get_contexts(project="my_project")
        # Returns: {"Departments": "Department master data", "Employees": "Employee data"}
    """
    headers = _create_request_header(api_key)
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    response = http.get(
        BASE_URL + f"/project/{project}/contexts",
        headers=headers,
    )
    contexts = response.json()
    contexts = {context["name"]: context["description"] for context in contexts}
    if prefix:
        contexts = {
            context: description
            for context, description in contexts.items()
            if context.startswith(prefix)
        }
    return contexts


def delete_context(
    name: str,
    *,
    delete_children: bool = True,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> None:
    """
    Delete a context from the server.

    Args:
        name: Name of the context to delete.

        delete_children: Whether to delete child contexts (which share the same "/" separated prefix).

        project: Name of the project the context belongs to.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.
    """
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    headers = _create_request_header(api_key)

    contexts_to_delete = [name]

    if delete_children:
        children = get_contexts(project, prefix=name + "/", api_key=api_key)
        contexts_to_delete.extend(children.keys())

    response = None
    for ctx in contexts_to_delete:
        response = http.delete(
            BASE_URL + f"/project/{project}/contexts/{ctx}",
            headers=headers,
        )
    if response is not None:
        return response.json()


def add_logs_to_context(
    log_ids: List[int],
    *,
    context: Optional[str] = None,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> None:
    """
    Add logs to a context.

    Args:
        log_ids: List of log ids to add to the context.

        context: Name of the context to add the logs to.

        project: Name of the project the logs belong to.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A message indicating whether the logs were successfully added to the context.
    """
    context = context if context else CONTEXT_WRITE.get()
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    headers = _create_request_header(api_key)
    body = {
        "context_name": context,
        "log_ids": log_ids,
    }
    response = http.post(
        BASE_URL + f"/project/{project}/contexts/add_logs",
        headers=headers,
        json=body,
    )
    return response.json()


def commit_context(
    name: str,
    commit_message: str,
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Creates a commit for a single context.

    Args:
        name: Name of the context to commit.
        commit_message: A description of the changes being saved.
        project: Name of the project the context belongs to.
        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing the new commit_hash.
    """
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    headers = _create_request_header(api_key)
    body = {"commit_message": commit_message}
    response = http.post(
        BASE_URL + f"/project/{project}/contexts/{name}/commit",
        headers=headers,
        json=body,
    )
    return response.json()


def rollback_context(
    name: str,
    commit_hash: str,
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Rolls back a single context to a specific commit.

    Args:
        name: Name of the context to roll back.
        commit_hash: The hash of the commit to restore.
        project: Name of the project the context belongs to.
        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A message indicating the success of the rollback operation.
    """
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    headers = _create_request_header(api_key)
    body = {"commit_hash": commit_hash}
    response = http.post(
        BASE_URL + f"/project/{project}/contexts/{name}/rollback",
        headers=headers,
        json=body,
    )
    return response.json()


def get_context_commits(
    name: str,
    *,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[Dict]:
    """
    Retrieves the commit history for a context.

    Args:
        name: Name of the context.
        project: Name of the project the context belongs to.
        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A list of dictionaries, each representing a commit.
    """
    project = _get_and_maybe_create_project(
        project,
        api_key=api_key,
        create_if_missing=False,
    )
    headers = _create_request_header(api_key)
    response = http.get(
        BASE_URL + f"/project/{project}/contexts/{name}/commits",
        headers=headers,
    )
    return response.json()
