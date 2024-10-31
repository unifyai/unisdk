import json

import unify
from typing import Optional, List, Dict, Any

from .system_messages import SUGGEST_SYS_MESSAGE


def _print_table_from_dicts(dcts, col_list=None) -> str:
    if not col_list:
        col_list = list(dcts[0].keys() if dcts else [])
    my_list = [col_list]
    for item in dcts:
        my_list.append(
            [str(item[col] if item[col] is not None else "") for col in col_list],
        )
    col_size = [max(map(len, col)) for col in zip(*my_list)]
    format_str = " | ".join(["{{:<{}}}".format(i) for i in col_size])
    my_list.insert(1, ["-" * i for i in col_size])
    ret = list()
    for item in my_list:
        ret.append(format_str.format(*item))
    return "\n".join(ret)


def _format_evals(evals: Dict[str, List[unify.Log]]) -> str:
    ret = list()
    for config_str, logs in evals.items():
        ret.append(
            "Configuration:\n" "--------------\n",
        )
        config = json.loads(config_str)
        for param_name, param_value in config.items():
            ret.append(param_name + ":\n")
            ret.append(param_value)
        ret.append(
            "\n" "Logs:\n" "-----\n",
        )
        ret.append(
            json.dumps([lg.to_json() for lg in logs], indent=4),
        )
    return "\n".join(ret)


def update(
    metric: str,
    mode: str = "maximize",
    interactive: bool = True,
    logs: Optional[List[unify.Log]] = None,
):
    """
    Make a suggestion for how to improve the performance of the metric specified by
    either the maximize or minimize

    Args:
        metric: The metric name that we're looking to optimize.

        mode: The optimization mode, either maximize or minimize for the metric.

        interactive: Whether to run in interactive mode, with a human in the loop.
        Default is True.

        logs: The logs to parse and use for the suggestion.

    Returns:
          The suggested parameter name to update, and the suggested new value.
    """
    # ToDo: add interactive support
    assert mode in ("maximize", "minimize"), "Mode must be 'maximize' or 'minimize'."

    client = unify.Unify("o1-preview@openai", cache=True)

    if not logs:
        logs = unify.get_logs()

    evals = unify.group_logs_by_configs(logs=logs)
    evals_str = _format_evals(evals)

    system_message = (
        SUGGEST_SYS_MESSAGE.replace(
            "{configs}",
            str(unify.get_params())[1:-1],
        )
        .replace(
            "{evals}",
            evals_str,
        )
        .replace(
            "{relation}",
            mode,
        )
        .replace(
            "{low|high}",
            "low" if mode == "maximize" else "high",
        )
        .replace(
            "{metric}",
            metric,
        )
    )
    response = client.generate(system_message)
    parameter = response.split("\nparameter:\n")[-1].split("\nvalue:\n")[0].strip("\n")
    value = (
        response.split(
            "\nvalue:\n",
        )[-1]
        .lstrip("```python")
        .lstrip("```")
        .rstrip("```")
        .lstrip(
            "\n",
        )
        .rstrip("\n")
    )
    return parameter, value, response
