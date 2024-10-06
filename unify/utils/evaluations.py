import requests
from typing import Optional, Any, Dict, Union, List

from unify import BASE_URL
from .helpers import _validate_api_key


def trigger_evaluation(
    evaluator: str,
    dataset: Union[str, int, List[int]],
    agent: str,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Trigger an evaluation for a specific dataset using a given evaluator and endpoint.

    Args:
        evaluator: Name of the evaluator to use.
        dataset: Name of the uploaded dataset to evaluate.
        agent: Name of the agent to evaluate, specified in `model@provider`.
        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing the response from the API.

    Raises:
        requests.HTTPError: If the API request fails.
        KeyError: If the API key is not provided and not set in the environment.
        FileNotFoundError: If the client_side_scores file is specified but not found.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{BASE_URL}/evaluation/trigger"

    params = {
        "evaluator": evaluator,
        "dataset": dataset,
        "agent": agent,
    }

    response = requests.post(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def upload_evaluations(
    evaluator: str,
    dataset: str,
    agent: str,
    evaluations: List[Dict],
    api_key: Optional[str] = None,
) -> None:
    """
    Uploads evaluation results to your user console.

    Args:
        evaluator: Name of the evaluator to use.
        dataset: Name of the uploaded dataset to evaluate.
        agent: Name of the agent to evaluate. Either specified using the
        `model@provider` format, or an arbitrary client-side agent.
        evaluations: The collection of evaluations to upload.
        api_key: If specified, unify API key to be used. Defaults to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing the response from the API.

    Raises:
        requests.HTTPError: If the API request fails.
        KeyError: If the API key is not provided and not set in the environment.
        FileNotFoundError: If the client_side_scores file is specified but not found.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{BASE_URL}/evaluation"

    params = {
        "evaluator": evaluator,
        "dataset": dataset,
        "endpoint": agent,
    }

    files = {"evaluations": evaluations}

    response = requests.post(url, headers=headers, params=params, files=files)
    response.raise_for_status()

    return response.json()


def get_evaluations(
    dataset: str,
    agent: Optional[str] = None,
    evaluator: Optional[str] = None,
    per_prompt: bool = False,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get evaluations for a specific dataset, optionally filtered by endpoint and evaluator.

    Args:
        dataset: Name of the dataset to fetch evaluation from.
        agent: The agent to fetch the evaluation for. If None, returns evaluations for all agents.
        evaluator: Name of the evaluator to fetch the evaluation for. If None, returns all available evaluations for the dataset and endpoint pair.
        per_prompt: If True, returns the scores on a per-prompt level. By default set to False. If True requires an eval name and endpoint to be set.
        api_key: If specified, unify API key to be used. Defaults to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing the evaluation results.

    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    url = f"{BASE_URL}/evaluation"

    params = {"dataset": dataset, "per_prompt": per_prompt}

    if agent:
        params["endpoint"] = agent
    if evaluator:
        params["evaluator"] = evaluator

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def delete_evaluations(
    dataset: str,
    endpoint: Optional[str] = None,
    evaluator: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Delete evaluations for a specific dataset, optionally filtered by endpoint and evaluator.

    Args:
        dataset: Name of the dataset to delete the evaluation for.
        endpoint: The endpoint to delete the evaluation for. If None, deletes the evaluations for all endpoints.
        evaluator: Name of the evaluator to delete the evaluation for. If None, deletes all available evaluations for the dataset and endpoint pair.
        api_key: If specified, unify API key to be used. Defaults to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing information about the deletion operation.

    Raises:
        requests.exceptions.RequestException: If the API request fails.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    url = f"{BASE_URL}/evaluation"

    params = {
        "dataset": dataset,
    }

    if endpoint:
        params["endpoint"] = endpoint
    if evaluator:
        params["evaluator"] = evaluator

    response = requests.delete(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()
