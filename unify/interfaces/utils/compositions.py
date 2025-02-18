from __future__ import annotations
import json

from ...utils.helpers import _validate_api_key
from .logs import _add_to_log, _to_log_ids
from .logs import *


# Helpers #
# --------#


def _replace_log_fields(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    mode: str = None,
    api_key: Optional[str] = None,
    **data,
) -> Dict[str, str]:
    assert mode in (
        "params",
        "entries",
    ), "mode must be one of 'params', 'entries'"
    api_key = _validate_api_key(api_key)
    for k, v in data.items():
        delete_log_fields(field=k, logs=logs, api_key=api_key)
    return _add_to_log(logs=logs, mode=mode, api_key=api_key, **data)


def _update_log_fields(
    *,
    fn: Union[callable, Dict[str, callable]],
    log: Optional[Union[int, unify.Log]] = None,
    mode: str = None,
    api_key: Optional[str] = None,
    **data,
) -> Dict[str, str]:
    assert mode in (
        "params",
        "entries",
    ), "mode must be one of 'params', 'entries'"
    old_data = getattr(get_log_by_id(id=_to_log_ids(log)[0], api_key=api_key), mode)
    replacements = dict()
    for k, v in data.items():
        f = fn[k] if isinstance(fn, dict) else fn
        replacements[k] = f(old_data[k], v)
    return _replace_log_fields(logs=log, mode=mode, api_key=api_key, **replacements)


# Parameters #
# -----------#


def replace_log_params(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    api_key: Optional[str] = None,
    **params,
) -> Dict[str, str]:
    """
    Replaces existing params in existing logs.

    Args:
        logs: The log(s) to replace fields for. Looks for the current active log if none
        specified.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        params: The params to update in the log.

    Returns:
        A message indicating whether the log(s) were successfully updated.
    """
    return _replace_log_fields(
        logs=logs,
        mode="params",
        api_key=api_key,
        **params,
    )


def update_log_params(
    *,
    fn: Union[callable, Dict[str, callable]],
    log: Optional[Union[int, unify.Log]] = None,
    api_key: Optional[str] = None,
    **params,
) -> Dict[str, str]:
    """
    Updates existing params in an existing log.

    Args:
        fn: The function or set of functions to apply to each field in the log.

        log: The log to update fields for. Looks for the current active log if not
        provided.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        params: The params to update in the log.

    Returns:
        A message indicating whether the log was successfully updated.
    """
    return _update_log_fields(
        fn=fn,
        log=log,
        mode="params",
        api_key=api_key,
        **params,
    )


def get_param_by_version(
    field: str,
    version: Union[str, int],
    api_key: Optional[str] = None,
) -> Any:
    """
    Gets the parameter by version.

    Args:
        field: The field of the parameter to get.

        version: The version of the parameter to get.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        The parameter by version.
    """
    api_key = _validate_api_key(api_key)
    version = str(version)
    filter_exp = f"version({field}) == {version}"
    return get_logs(filter=filter_exp, limit=1, api_key=api_key)[0].params[field][1]


def get_param_by_value(
    field: str,
    value: Any,
    api_key: Optional[str] = None,
) -> Any:
    """
    Gets the parameter by value.

    Args:
        field: The field of the parameter to get.

        value: The value of the parameter to get.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        The parameter by version.
    """
    api_key = _validate_api_key(api_key)
    filter_exp = f"{field} == {json.dumps(value)}"
    return get_logs(filter=filter_exp, limit=1, api_key=api_key)[0].params[field][0]


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


# Entries #
# --------#


def replace_log_entries(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    api_key: Optional[str] = None,
    **entries,
) -> Dict[str, str]:
    """
    Replaces existing entries in existing logs.

    Args:
        logs: The log(s) to replace fields for. Looks for the current active log if none
        specified.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        entries: The entries to replace in the log.

    Returns:
        A message indicating whether the logs were successfully updated.
    """
    return _replace_log_fields(logs=logs, mode="entries", api_key=api_key, **entries)


def update_log_entries(
    *,
    fn: Union[callable, Dict[str, callable]],
    log: Optional[Union[int, unify.Log]] = None,
    api_key: Optional[str] = None,
    **entries,
) -> Dict[str, str]:
    """
    Updates existing entries in an existing log.

    Args:
        fn: The function or set of functions to apply to each field in the log.

        log: The log to update fields for. Looks for the current active log if not
        provided.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        entries: The entries to update in the log.

    Returns:
        A message indicating whether the log was successfully updated.
    """
    return _update_log_fields(
        fn=fn,
        log=log,
        mode="entries",
        api_key=api_key,
        **entries,
    )
