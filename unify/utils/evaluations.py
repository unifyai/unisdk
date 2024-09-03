import json
import requests
from typing import Optional, List

from unify import base_url
from unify.helpers import _validate_api_key, _res_to_list


def trigger_evaluation(
    dataset: str, endpoints: List[str], api_key: Optional[str] = None
) -> str:
    """
    Evaluates a list of endpoint on a given dataset.

    Args:
        dataset: Name of the dataset to be uploaded.
        endpoints: List of endpoints.
        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        Info msg with the response from the HTTP endpoint.
    Raises:
        ValueError: If there was an HTTP error.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    for endpoint in endpoints:
        data = {"dataset": dataset, "endpoint": endpoint}
        # Send POST request to the /evaluation endpoint
        response = requests.post(
            base_url() + "/evaluation", headers=headers, params=data
        )
        if response.status_code != 200:
            raise ValueError(f"Error in endpoint {endpoint}: {response.text}")
    return json.loads(response.text)["info"]


def get_evaluations(
    dataset: Optional[str] = None, api_key: Optional[str] = None
) -> List[str]:
    """
    Fetches a list of all evaluations.

    Args:
        dataset: Name of the dataset to fetch evaluation from. If not specified, all
        evaluations will be returned.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        List with the names of the uploaded datasets.
    Raises:
        ValueError: If there was an HTTP error.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    params = {"dataset": dataset}
    # Send GET request to the /evaluation/list endpoint
    response = requests.get(base_url() + "/evaluation", params=params, headers=headers)
    if response.status_code != 200:
        raise ValueError(response.text)
    return _res_to_list(response)


def delete_evaluations(name: str, endpoint: str, api_key: Optional[str] = None) -> str:
    """
    Deletes an evaluation from the platform.

    Args:
        name: Name of the dataset in the evaluation.
        endpoint: Name of the endpoint whose evaluation will be removed.
        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        Info msg with the response from the HTTP endpoint.
    Raises:
        ValueError: If there was an HTTP error.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    params = {"dataset": name, "endpoint": endpoint}
    # Send DELETE request to the /evaluation endpoint
    response = requests.delete(
        base_url() + "/evaluation", headers=headers, params=params
    )
    if response.status_code != 200:
        raise ValueError(response.text)
    return json.loads(response.text)["info"]


def eval_status():
    raise NotImplementedError
