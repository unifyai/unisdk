from __future__ import annotations

from .logs import *


def get_source() -> str:
    """
    Extracts the source code for the file from where this function was called.

    Returns:
        The source code for the file, as a string.
    """
    frame = inspect.getouterframes(inspect.currentframe())[1]
    with open(frame.filename, "r") as file:
        source = file.read()
    return f"```python\n{source}\n```"


# Experiments #
# ------------#


def get_experiment_name(version: int, api_key: Optional[str] = None) -> str:
    """
    Gets the experiment name (by version).

    Args:
        version: The version of the experiment to get.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        The experiment name with said version.
    """
    experiments = get_groups(key="experiment", api_key=api_key)
    if not experiments:
        return None
    elif version < 0:
        version = len(experiments) + version
    if str(version) not in experiments:
        return None
    return experiments[str(version)]


def get_experiment_version(name: str, api_key: Optional[str] = None) -> int:
    """
    Gets the experiment version (by name).

    Args:
        name: The name of the experiment to get.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        The experiment version with said name.
    """
    experiments = get_groups(key="experiment", api_key=api_key)
    if not experiments:
        return None
    experiments = {v: k for k, v in experiments.items()}
    if name not in experiments:
        return None
    return int(experiments[name])
