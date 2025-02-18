import requests
from typing import Optional, Dict, Any
from ...utils.helpers import _validate_api_key, _get_and_maybe_create_project

from unify import BASE_URL
from .contexts import *


# Datasets #
# ---------#


def list_datasets(
    *,
    project: Optional[str] = None,
    prefix: str = "",
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    List all datasets associated with a project and context.

    Args:
        project: Name of the project the datasets belong to.

        prefix: Prefix of the datasets to get.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A list of datasets.
    """
    api_key = _validate_api_key(api_key)
    contexts = get_contexts(
        prefix=f"Datasets/{prefix}",
        project=project,
        api_key=api_key,
    )
    return {
        "/".join(name.split("/")[1:]): description
        for name, description in contexts.items()
    }
