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


def _format_evals(evals: Dict[str, List[Dict[str, Any]]]) -> str:
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
            json.dumps(logs, indent=4),
        )
    return "\n".join(ret)


def suggest(
    metric: str,
    mode: str = "maximize",
    logs: Optional[List[unify.Log]] = None,
):
    """
    Make a suggestion for how to improve the performance of the metric specified by
    either the maximize or minimize

    Args:
        metric: The metric name that we're looking to optimize.

        mode: The optimization mode, either maximize or minimize for the metric.

        logs: The logs to parse and use for the suggestion.

    Returns:
          The suggested parameter name to update, and the suggested new value.
    """
    assert mode in ("maximize", "minimize"), "Mode must be 'maximize' or 'minimize'."

    client = unify.Unify("gpt-4o@openai", cache=True)

    if not logs:
        logs = unify.get_logs()

    # ToDo: remove hard-coding once REST API is complete
    config = unify.Config(
        evaluator_code="'def evaluate_response(question: str, response: str) -> float:\n    correct_answer = eval(question)\n    try:\n        response_int = int(\n            "
        ".join([c for c in response.split("
        ")[-1] if c.isdigit()]),\n        )\n        return float(correct_answer == response_int)\n    except ValueError:\n        return 0.\n'",
    )
    for lg in logs:
        if "evaluator_code" in lg.entries:
            del lg.entries["evaluator_code"]
        lg._config = config
    # End ToDo

    evals = unify.group_logs_by_config(logs)
    # ToDo: fix this hack once ordering is correctly preserved
    evals = {
        k: [
            {
                "question": lg.entries["question"],
                "response": lg.entries["response"],
                "score": lg.entries["score"],
            }
            for lg in logs
        ]
        for k, logs in evals.items()
    }
    # End ToDo
    evals_str = _format_evals(evals)

    system_message = (
        SUGGEST_SYS_MESSAGE.replace(
            "{configs}",
            str(list(config.parameters.keys()))[1:-1],
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
    response = client.generate(
        "please follow the instructions of the system message",
        system_message=system_message,
    )
    breakpoint()
    return response
