import json
import os
from typing import List, Optional, Tuple

import requests
from unify.exceptions import UnifyError

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


def _res_to_list(response: requests.Response) -> List[str]:
    return json.loads(response.text)


def list_models() -> List[str]:
    """
    Get a list of available models.

    Returns:
        List[str]: A list of available model names if successful, otherwise an empty list.
    Raises:
        BadRequestError: If there was an HTTP error.
        ValueError: If there was an error parsing the JSON response.
    """
    url = f"{_base_url}/models"
    return _res_to_list(requests.get(url))


def list_endpoints(model: str) -> List[str]:
    """
    Get a list of endpoints for a specific model.

    Args:
        model (str): The name of the model.

    Returns:
        List[str]: A list of endpoint names associated with the model if successful,
        otherwise an empty list.
    Raises:
        BadRequestError: If there was an HTTP error.
        ValueError: If there was an error parsing the JSON response.
    """
    url = f"{_base_url}/endpoints_of"
    return _res_to_list(requests.get(url, params={"model": model}))


def list_providers(model: str) -> List[str]:
    """
    Get a list of providers for a specific model.

    Args:
        model (str): The name of the model.

    Returns:
        List[str]: A list of provider names associated with the model if successful,
        otherwise an empty list.
    Raises:
        BadRequestError: If there was an HTTP error.
        ValueError: If there was an error parsing the JSON response.
    """
    url = f"{_base_url}/providers_of"
    return _res_to_list(requests.get(url, params={"model": model}))


def _validate_api_key(api_key: Optional[str]) -> str:
    if api_key is None:
        api_key = os.environ.get("UNIFY_KEY")
    if api_key is None:
        raise KeyError(
            "UNIFY_KEY is missing. Please make sure it is set correctly!",
        )
    return api_key


def _validate_endpoint_name(value: str) -> Tuple[str, str]:
    error_message = "endpoint string must use OpenAI API format: <uploaded_by>/<model_name>@<provider_name>"  # noqa: E501

    if not isinstance(value, str):
        raise UnifyError(error_message)

    try:
        model_name, provider_name = value.split("/")[-1].split("@")
    except ValueError:
        raise UnifyError(error_message)

    if not model_name or not provider_name:
        raise UnifyError(error_message)
    return (model_name, provider_name)


def _validate_endpoint(  # noqa: WPS231
    endpoint: Optional[str] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
) -> Tuple[str, str, Optional[str]]:
    error_message = (
        "You must either provide an endpoint or the model and provider names!"
    )
    if endpoint:
        if model or provider:
            raise UnifyError(error_message)
        model, provider = _validate_endpoint_name(endpoint)  # noqa: WPS414
    else:
        if not model or not provider:
            raise UnifyError(error_message)
        endpoint = "@".join([model, provider])

    if provider in _available_dynamic_modes:
        provider = None
    return endpoint, model, provider
