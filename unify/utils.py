import os
from typing import Optional, Tuple

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
