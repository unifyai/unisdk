import json

import unify
from typing import Optional, List

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


def _get_evals(logs: List[unify.Log], metric: str) -> str:

    evals = {
        k: [lg.to_json()["entries"] for lg in v]
        for k, v in sorted(
            unify.group_logs_by_configs(logs=logs).items(),
            key=lambda item: sum([lg.entries[metric] for lg in item[1]]) / len(item[1]),
        )
    }
    highest_performing_entry_metrics = set(
        [entry[metric] for entry in list(evals.values())[-1]],
    )
    evals_pruned = dict()
    for i, (config_str, entries) in enumerate(reversed(evals.items())):
        evals_pruned[config_str] = list()
        for entry in entries:
            if i > 0 and entry[metric] in highest_performing_entry_metrics:
                continue
            evals_pruned[config_str].append(entry)
    evals_pruned = {k: v for k, v in reversed(evals_pruned.items())}

    ret = list()
    for i, (config_str, entries) in enumerate(evals_pruned.items()):
        ret.append(
            f"Experiment {i}:\n" + len(str(i)) * "=" + "============\n",
        )
        ret.append(
            " " * 4 + "Parameters:\n" "    -----------",
        )
        config = json.loads(config_str)
        for param_name, param_value in config.items():
            ret.append("\n    **" + param_name + "**:")
            ret.append(" " * 4 + json.dumps(param_value))
        ret.append(
            "\n" "    Logs:\n" "    -----",
        )
        ret.append(
            " " * 4
            + json.dumps(
                sorted(entries, key=lambda entry: entry[metric]),
                indent=4,
            )
            .replace("[", "")
            .replace("]", ""),
        )
        ret.append(
            "\n"
            f"    Mean {metric.capitalize()}:\n    " + "-" * len(metric) + "------",
        )
        ret.append(
            " " * 4
            + json.dumps(sum([entry[metric] for entry in entries]) / len(entries))
            + "\n",
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

    system_message = (
        SUGGEST_SYS_MESSAGE.replace(
            "{configs}",
            str(unify.get_params())[1:-1],
        )
        .replace(
            "{evals}",
            _get_evals(logs, metric),
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
