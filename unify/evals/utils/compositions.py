from __future__ import annotations
import json

from ...utils.helpers import _validate_api_key, _get_and_maybe_create_project
from .logging import _add_to_log
from .logging import *


# Helpers #
# --------#


def _replace_log_fields(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    mode: str = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    assert mode in (
        "parameters",
        "entries",
    ), "mode must be one of 'parameters', 'entries'"
    log_id = logs  # handle_multiple_logs decorator handles logs, returning a single id
    api_key = _validate_api_key(api_key)
    for k, v in kwargs.items():
        delete_log_fields(field=k, logs=log_id, api_key=api_key)
    return _add_to_log(logs=log_id, mode=mode, api_key=api_key, **kwargs)


def _update_log_fields(
    *,
    fn: Union[callable, Dict[str, callable]],
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    mode: str = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    assert mode in (
        "parameters",
        "entries",
    ), "mode must be one of 'parameters', 'entries'"
    log_id = logs  # handle_multiple_logs decorator handles logs, returning a single id
    data = getattr(get_log_by_id(id=log_id, api_key=api_key), mode)
    replacements = dict()
    for k, v in kwargs.items():
        f = fn[k] if isinstance(fn, dict) else fn
        replacements[k] = f(data[k], v)
    return _replace_log_fields(logs=log_id, mode=mode, api_key=api_key, **replacements)


def _rename_log_fields(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    mode: str = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    assert mode in (
        "parameters",
        "entries",
    ), "mode must be one of 'parameters', 'entries'"
    log_id = logs  # handle_multiple_logs decorator handles logs, returning a single id
    api_key = _validate_api_key(api_key)
    data = getattr(get_log_by_id(id=log_id, api_key=api_key), mode)
    for old_name in kwargs.keys():
        delete_log_fields(field=old_name, logs=log_id, api_key=api_key)
    new_data = {new_name: data[old_name] for old_name, new_name in kwargs.items()}
    return _add_to_log(logs=log_id, mode=mode, api_key=api_key, **new_data)


# Parameters #
# -----------#


def replace_log_parameters(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    """
    Replaces existing parameters in an existing log.

    Args:
        logs: The log(s) to replace fields for. Looks for the current active log if none
        specified.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: The data to update in the log.

    Returns:
        A message indicating whether the log was successfully updated.
    """
    return _replace_log_fields(logs=logs, mode="parameters", api_key=api_key, **kwargs)


def update_log_parameters(
    *,
    fn: Union[callable, Dict[str, callable]],
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    """
    Updates existing parameters in an existing log.

    Args:
        fn: The function or set of functions to apply to each field in the log.

        logs: The log(s) to update fields for. Looks for the current active log if not
        provided.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: The data to update in the log.

    Returns:
        A message indicating whether the log was successfully updated.
    """
    return _update_log_fields(
        fn=fn,
        logs=logs,
        mode="parameters",
        api_key=api_key,
        **kwargs,
    )


def rename_log_parameters(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    """
    Renames the set of log parameters.

    Args:
        logs: The log(s) to update the field names for. Looks for the current active log
        if none are provided.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: The field names to update in the log, with keys as old names and values
        as new names.

    Returns:
        A message indicating whether the log field names were successfully updated.
    """
    return _rename_log_fields(logs=logs, mode="parameters", api_key=api_key, **kwargs)


def group_logs_by_parameters(
    *,
    logs: List[unify.Log],
) -> Dict:
    configs = list(dict.fromkeys([json.dumps(lg.parameters) for lg in logs]))
    ret_dict = dict()
    for conf in configs:
        ret_dict[conf] = [lg for lg in logs if json.dumps(lg.parameters) == conf]
    return ret_dict


# Entries #
# --------#


def replace_log_entries(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    """
    Replaces existing entries in an existing log.

    Args:
        logs: The log(s) to replace fields for. Looks for the current active log if none
        specified.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: The data to update in the log.

    Returns:
        A message indicating whether the log was successfully updated.
    """
    return _replace_log_fields(logs=logs, mode="entries", api_key=api_key, **kwargs)


def update_log_entries(
    *,
    fn: Union[callable, Dict[str, callable]],
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    """
    Updates existing entries in an existing log.

    Args:
        fn: The function or set of functions to apply to each field in the log.

        logs: The log(s) to update fields for. Looks for the current active log if not
        provided.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: The data to update in the log.

    Returns:
        A message indicating whether the log was successfully updated.
    """
    return _update_log_fields(
        fn=fn,
        logs=logs,
        mode="entries",
        api_key=api_key,
        **kwargs,
    )


def rename_log_entries(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    """
    Renames the set of log entries.

    Args:
        logs: The log(s) to update the field names for. Looks for the current active log
        if none are provided.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: The field names to update in the log, with keys as old names and values
        as new names.

    Returns:
        A message indicating whether the log field names were successfully updated.
    """
    return _rename_log_fields(logs=logs, mode="entries", api_key=api_key, **kwargs)


# Fields (Both) #
# --------------#


# noinspection PyShadowingBuiltins
def delete_logs_by_value(
    *,
    project: Optional[str] = None,
    filter: Optional[str] = None,
    api_key: Optional[str] = None,
):
    """
    Returns a list of filtered logs from a project.

    Args:
        project: Name of the project to delete logs from.

        filter: Boolean string to filter logs for deletion, for example:
        "(temperature > 0.5 and (len(system_msg) < 100 or 'no' in usr_response))"

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        The list of deleted logs for the project, after optionally applying filtering.
    """
    logs = get_logs(project=project, filter=filter, api_key=api_key)
    for lg in logs:
        lg.delete()
    return logs


def get_logs_with_fields(
    *fields: str,
    mode: str = "all",
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[unify.Log]:
    """
    Returns a list of logs which contain the specified fields, either the logs which
    contain all of them ("all") or the logs which contain any of the fields ("any").

    Args:
        fields: The fields to retrieve logs for.

        mode: The retrieval mode, either returning the logs with all of the fields or
        the logs with any of the fields.

        project: Name of the project to get logs from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A list of logs which contain the specified fields.
    """
    api_key = _validate_api_key(api_key)
    mode = {"any": "or", "all": "and"}[mode]
    filter_exp = f" {mode} ".join([f"exists({field})" for field in fields])
    return get_logs(project=project, filter=filter_exp, api_key=api_key)


def get_logs_without_fields(
    *fields: str,
    mode: str = "all",
    project: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[unify.Log]:
    """
    Returns a list of logs which do not contain the specified fields, either the logs
    which do not contain all of the fields ("all") or the logs which do not contain any
    of the fields ("any").

    Args:
        fields: The fields to not retrieve logs for.

        mode: The retrieval mode, either returning the logs with do not contain all of
        the fields or the logs which do not contain any of the fields.

        project: Name of the project to get logs from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A list of logs which do not contain the specified fields.
    """
    api_key = _validate_api_key(api_key)
    mode = {"any": "and", "all": "or"}[mode]
    filter_exp = f" {mode} ".join([f"(not exists({field}))" for field in fields])
    return get_logs(project=project, filter=filter_exp, api_key=api_key)


def get_logs_by_value(
    *,
    project: str,
    api_key: Optional[str] = None,
    **kwargs,
) -> List[unify.Log]:
    """
    Returns the logs with the data matching exactly if it exists,
    otherwise returns None.

    Args:
        project: Name of the project to get logs from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        Whether or not to include logs which contain identical key-value pairs to all
        kwargs passed which are present in the log, but

        kwargs: The data to search the upstream logs for.

    Returns:
        The list of unify.Logs which match the data, if any exist.
    """
    filter_str = " and ".join(
        [
            f"({k} == {json.dumps(v) if isinstance(v, str) else v})"
            for k, v in kwargs.items()
        ],
    )
    return get_logs(project=project, filter=filter_str, api_key=api_key)


def get_log_by_value(
    *,
    project: str,
    api_key: Optional[str] = None,
    **kwargs,
) -> Optional[unify.Log]:
    """
    Returns the log with the data matching exactly if it exists,
    otherwise returns None.

    Args:
        project: Name of the project to get logs from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        kwargs: The data to search the upstream logs for.

    Returns:
        The single unify.Log which matches the data, if it exists.
    """
    logs = get_logs_by_value(project=project, **kwargs, api_key=api_key)
    assert len(logs) in (
        0,
        1,
    ), "Expected exactly zero or one log, but found {len(logs)}"
    return logs[0] if logs else None


def group_logs(
    *,
    key: str,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
):
    """
    Groups logs based on equality '==' of the values for the specified key, returning a
    dict with group indices as the keys and the list of logs as the values. If the keys
    are not versioned, then the indices are simply incrementing integers.

    Args:
        key: Name of the log entry to do equality matching for.

        project: Name of the project to get logs from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A dict containing the grouped logs, with each key of the dict representing the
        version of the log key with equal values, and the value being a list of logs.
    """
    api_key = _validate_api_key(api_key)
    project = _get_and_maybe_create_project(project, api_key=api_key)
    return {
        k: get_logs(
            project=project,
            filter="{} == {}".format(key, '"' + v + '"' if isinstance(v, str) else v),
            api_key=api_key,
        )
        for k, v in get_groups(key=key, project=project, api_key=api_key).items()
    }
