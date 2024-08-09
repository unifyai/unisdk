import os
import json
import requests
from typing import Dict, List, Optional

_available_dynamic_modes = [
    "lowest-input-cost",
    "input-cost",
    "lowest-output-cost",
    "output-cost",
    "lowest-itl",
    "itl",
    "lowest-ttft",
    "ttft",
    "highest-tks-per-sec",
    "tks-per-sec",
]

_base_url = "https://api.unify.ai/v0"


def _res_to_list(response: requests.Response) -> List:
    return json.loads(response.text)


def _validate_api_key(api_key: Optional[str]) -> str:
    if api_key is None:
        api_key = os.environ.get("UNIFY_KEY")
    if api_key is None:
        raise KeyError(
            "UNIFY_KEY is missing. Please make sure it is set correctly!",
        )
    return api_key


def list_models(
    provider: Optional[str] = None, api_key: Optional[str] = None
) -> List[str]:
    """
    Get a list of available models, either in total or for a specific provider.

    Args:
        provider (str): If specified, returns the list of models supporting this provider.
        api_key (str): If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        List[str]: A list of available model names if successful, otherwise an empty list.
    Raises:
        BadRequestError: If there was an HTTP error.
        ValueError: If there was an error parsing the JSON response.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{_base_url}/models"
    if provider:
        return _res_to_list(
            requests.get(url, headers=headers, params={"provider": provider})
        )
    return _res_to_list(requests.get(url, headers=headers))


def list_providers(
    model: Optional[str] = None, api_key: Optional[str] = None
) -> List[str]:
    """
    Get a list of available providers, either in total or for a specific model.

    Args:
        model (str): If specified, returns the list of providers supporting this model.
        api_key (str): If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        List[str]: A list of provider names associated with the model if successful,
        otherwise an empty list.
    Raises:
        BadRequestError: If there was an HTTP error.
        ValueError: If there was an error parsing the JSON response.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{_base_url}/providers"
    if model:
        return _res_to_list(requests.get(url, headers=headers, params={"model": model}))
    return _res_to_list(requests.get(url, headers=headers))


def list_endpoints(
    model: Optional[str] = None,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[str]:
    """
    Get a list of available endpoint, either in total or for a specific model or provider.

    Args:
        model (str): If specified, returns the list of endpoint supporting this model.
        provider (str): If specified, returns the list of endpoint supporting this provider.
        api_key (str): If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        List[str]: A list of endpoint names if successful, otherwise an empty list.
    Raises:
        BadRequestError: If there was an HTTP error.
        ValueError: If there was an error parsing the JSON response.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{_base_url}/endpoints"
    if model and provider:
        raise ValueError("Please specify either model OR provider, not both.")
    elif model:
        return _res_to_list(requests.get(url, headers=headers, params={"model": model}))
    elif provider:
        return _res_to_list(
            requests.get(url, headers=headers, params={"provider": provider})
        )
    return _res_to_list(requests.get(url, headers=headers))


def upload_dataset_from_file(
    name: str, path: str, api_key: Optional[str] = None
) -> str:
    """
    Uploads a local file as a dataset to the platform.

    Args:
        name (str): Name given to the uploaded dataset.
        path (str): Path to the file to be uploaded.
        api_key (str): If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        str: Info msg with the response from the HTTP endpoint.
    Raises:
        ValueError: If there was an HTTP error.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    with open(path, "rb") as f:
        file_content = f.read()
    files = {"file": ("dataset", file_content, "application/x-jsonlines")}
    data = {"name": name}
    # Send POST request to the /dataset endpoint
    response = requests.post(
        _base_url + "/dataset", headers=headers, data=data, files=files
    )
    if response.status_code != 200:
        raise ValueError(response.text)
    return json.loads(response.text)["info"]


def upload_dataset_from_dictionary(
    name: str, content: List[Dict[str, str]], api_key: Optional[str] = None
) -> str:
    """
    Uploads a list of dictionaries as a dataset to the platform.
    Each dictionary in the list must contain a `prompt` key.

    Args:
        name (str): Name given to the uploaded dataset.
        content List[Dict[str, str]]: Path to the file to be uploaded.
        api_key (str): If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        str: Info msg with the response from the HTTP endpoint.
    Raises:
        ValueError: If there was an HTTP error.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    content_str = "\n".join([json.dumps(d) for d in content])
    files = {"file": ("dataset", content_str, "application/x-jsonlines")}
    data = {"name": name}
    # Send POST request to the /dataset endpoint
    response = requests.post(
        _base_url + "/dataset", headers=headers, data=data, files=files
    )
    if response.status_code != 200:
        raise ValueError(response.text)
    return json.loads(response.text)["info"]


def delete_dataset(name: str, api_key: Optional[str] = None) -> str:
    """
    Deletes a dataset from the platform.

    Args:
        name (str): Name given to the uploaded dataset.
        path (str): Path to the file to be uploaded.
        api_key (str): If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        str: Info msg with the response from the HTTP endpoint.
    Raises:
        ValueError: If there was an HTTP error.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    params = {"name": name}
    # Send DELETE request to the /dataset endpoint
    response = requests.delete(_base_url + "/dataset", headers=headers, params=params)
    if response.status_code != 200:
        raise ValueError(response.text)
    return json.loads(response.text)["info"]


def download_dataset(
    name: str, path: Optional[str] = None, api_key: Optional[str] = None
) -> Optional[str]:
    """
    Downloads a dataset from the platform.

    Args:
        name (str): Name of the dataset to download.
        path (str): If specified, path to save the dataset.
        api_key (str): If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        str: If path is not specified, returns the dataset content, if
        specified, returns None.
    Raises:
        ValueError: If there was an HTTP error.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    params = {"name": name}
    # Send GET request to the /dataset endpoint
    response = requests.get(_base_url + "/dataset", headers=headers, params=params)
    if response.status_code != 200:
        raise ValueError(response.text)
    if path:
        with open(path, "w+") as f:
            f.write("\n".join([json.dumps(d) for d in json.loads(response.text)]))
            return None
    return json.loads(response.text)


def list_datasets(api_key: Optional[str] = None) -> List[str]:
    """
    Fetches a list of all uploaded datasets.

    Args:
        api_key (str): If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        List[str]: List with the names of the uploaded datasets.
    Raises:
        ValueError: If there was an HTTP error.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    # Send GET request to the /dataset/list endpoint
    response = requests.get(_base_url + "/dataset/list", headers=headers)
    if response.status_code != 200:
        raise ValueError(response.text)
    return _res_to_list(response)


def evaluate(dataset: str, endpoints: List[str], api_key: Optional[str] = None) -> str:
    """
    Evaluates a list of endpoint on a given dataset.

    Args:
        name (str): Name of the dataset to be uploaded.
        endpoint List[str]: List of endpoint.
        api_key (str): If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        str: Info msg with the response from the HTTP endpoint.
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
            _base_url + "/evaluation", headers=headers, params=data
        )
        if response.status_code != 200:
            raise ValueError(f"Error in endpoint {endpoint}: {response.text}")
    return json.loads(response.text)["info"]


def delete_evaluation(name: str, endpoint: str, api_key: Optional[str] = None) -> str:
    """
    Deletes an evaluation from the platform.

    Args:
        name (str): Name of the dataset in the evaluation.
        endpoint (str): Name of the endpoint whose evaluation will be removed.
        api_key (str): If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        str: Info msg with the response from the HTTP endpoint.
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
        _base_url + "/evaluation", headers=headers, params=params
    )
    if response.status_code != 200:
        raise ValueError(response.text)
    return json.loads(response.text)["info"]


def list_evaluations(
    dataset: Optional[str] = None, api_key: Optional[str] = None
) -> List[str]:
    """
    Fetches a list of all evaluations.

    Args:
        dataset (str): Name of the dataset to fetch evaluation from.
        If not specified, all evaluations will be returned.
        api_key (str): If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        List[Dict[str, List[str]]]: List with the names of the uploaded datasets.
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
    response = requests.get(_base_url + "/evaluation/list", headers=headers)
    if response.status_code != 200:
        raise ValueError(response.text)
    return _res_to_list(response)


def get_credits(api_key: Optional[str] = None) -> float:
    """
    Returns the credits remaining in the user account, in USD.

    Args:
        api_key (str): If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        float: The credits remaining in USD.
    Raises:
        ValueError: If there was an HTTP error.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    # Send GET request to the /get_credits endpoint
    response = requests.get(_base_url + "/get_credits", headers=headers)
    if response.status_code != 200:
        raise ValueError(response.text)
    return _res_to_list(response)["credits"]
