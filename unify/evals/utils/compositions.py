from __future__ import annotations
import json

from ...utils.helpers import _validate_api_key, _get_and_maybe_create_project
from .logging import _add_to_log, _to_log_ids, _to_logs
from .logging import *


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


def _rename_log_fields(
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
    for old_name in data.keys():
        delete_log_fields(field=old_name, logs=logs, api_key=api_key)
    new_data = {new_name: data[old_name] for old_name, new_name in data.items()}
    return _add_to_log(logs=logs, mode=mode, api_key=api_key, **new_data)


# Parameters #
# -----------#


def replace_log_params(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    api_key: Optional[str] = None,
    **params,
) -> Dict[str, str]:
    """
    Replaces existing params in an existing log.

    Args:
        logs: The log(s) to replace fields for. Looks for the current active log if none
        specified.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        params: The data to update in the log.

    Returns:
        A message indicating whether the log was successfully updated.
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

        params: The data to update in the log.

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


def rename_log_params(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    api_key: Optional[str] = None,
    **params,
) -> Dict[str, str]:
    """
    Renames the set of log params.

    Args:
        logs: The log(s) to update the field names for. Looks for the current active log
        if none are provided.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        params: The field names to update in the log, with keys as old names and values
        as new names.

    Returns:
        A message indicating whether the log field names were successfully updated.
    """
    return _rename_log_fields(
        logs=logs,
        mode="params",
        api_key=api_key,
        **params,
    )


def group_logs_by_configs(
    *,
    logs: List[unify.Log],
) -> Dict:
    configs = list(dict.fromkeys([json.dumps(lg.params) for lg in logs]))
    ret_dict = dict()
    for conf in configs:
        ret_dict[conf] = [lg for lg in logs if json.dumps(lg.params) == conf]
    return ret_dict


def add_param(
    *,
    logs: Optional[Union[str, int, unify.Log, List[Union[int, unify.Log]]]] = "all",
    api_key: Optional[str] = None,
    **param,
) -> Dict[str, str]:
    """
    Adds a new parameter to the logs (defaults to all logs).
    """
    if logs == "all":
        logs = get_logs()
    assert len(param) == 1, "Only one parameter is allowed when calling add_param"
    return add_log_params(logs=logs, api_key=api_key, **param)


def get_params(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = "all",
    api_key: Optional[str] = None,
) -> List[str]:
    """
    Gets all parameter names within the collection of logs (default to all logs).
    """
    if logs == "all":
        logs = get_logs(api_key=api_key)
    else:
        logs = _to_logs(logs)
    return list(dict.fromkeys([p for lg in logs for p in lg.params.keys()]))


def get_source():
    frame = inspect.getouterframes(inspect.currentframe())[1]
    with open(frame.filename, "r") as file:
        source = file.read()
    return source


# Entries #
# --------#


def replace_log_entries(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    api_key: Optional[str] = None,
    **entries,
) -> Dict[str, str]:
    """
    Replaces existing entries in an existing log.

    Args:
        logs: The log(s) to replace fields for. Looks for the current active log if none
        specified.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        entries: The data to update in the log.

    Returns:
        A message indicating whether the log was successfully updated.
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

        entries: The data to update in the log.

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


def rename_log_entries(
    *,
    logs: Optional[Union[int, unify.Log, List[Union[int, unify.Log]]]] = None,
    api_key: Optional[str] = None,
    **entries,
) -> Dict[str, str]:
    """
    Renames the set of log entries.

    Args:
        logs: The log(s) to update the field names for. Looks for the current active log
        if none are provided.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        entries: The field names to update in the log, with keys as old names and values
        as new names.

    Returns:
        A message indicating whether the log field names were successfully updated.
    """
    return _rename_log_fields(logs=logs, mode="entries", api_key=api_key, **entries)


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


def get_logs_by_id(
    ids: Union[int, List[int]],
    *,
    api_key: Optional[str] = None,
) -> List[unify.Log]:
    """
    Returns the logs associated with a given ids.

    Args:
        ids: IDs of the logs to fetch.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        The full set of logs matching the given ids.
    """
    if isinstance(ids, int):
        ids = [ids]
    return [get_log_by_id(id=i, api_key=api_key) for i in ids]


def get_logs_by_value(
    *,
    project: str,
    api_key: Optional[str] = None,
    **data,
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

        data: The data to search the upstream logs for.

    Returns:
        The list of unify.Logs which match the data, if any exist.
    """
    filter_str = " and ".join(
        [
            f"({k} == {json.dumps(v) if isinstance(v, str) else v})"
            for k, v in data.items()
        ],
    )
    return get_logs(project=project, filter=filter_str, api_key=api_key)


def get_log_by_value(
    *,
    project: str,
    api_key: Optional[str] = None,
    **data,
) -> Optional[unify.Log]:
    """
    Returns the log with the data matching exactly if it exists,
    otherwise returns None.

    Args:
        project: Name of the project to get logs from.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

        data: The data to search the upstream logs for.

    Returns:
        The single unify.Log which matches the data, if it exists.
    """
    logs = get_logs_by_value(project=project, **data, api_key=api_key)
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
