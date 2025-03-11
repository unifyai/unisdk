import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel
from unify import BASE_URL
from unify.utils import _requests

from ...utils.helpers import _validate_api_key


class Metrics(BaseModel, extra="allow"):
    ttft: Optional[float]
    itl: Optional[float]
    input_cost: Optional[float]
    output_cost: Optional[float]
    measured_at: Union[datetime.datetime, str, Dict[str, Union[datetime.datetime, str]]]


def get_endpoint_metrics(
    endpoint: str,
    *,
    start_time: Optional[Union[datetime.datetime, str]] = None,
    end_time: Optional[Union[datetime.datetime, str]] = None,
    api_key: Optional[str] = None,
) -> List[Metrics]:
    """
    Retrieve the set of cost and speed metrics for the specified endpoint.

    Args:
        endpoint: The endpoint to retrieve the metrics for, in model@provider format

        start_time: Window start time. Only returns the latest benchmark if unspecified.

        end_time: Window end time. Assumed to be the current time if this is unspecified
        and start_time is specified. Only the latest benchmark is returned if both are
        unspecified.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.

    Returns:
        The set of metrics for the specified endpoint.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    params = {
        "model": endpoint.split("@")[0],
        "provider": endpoint.split("@")[1],
        "start_time": start_time,
        "end_time": end_time,
    }
    response = _requests.get(
        BASE_URL + "/endpoint-metrics",
        headers=headers,
        params=params,
    )
    if response.status_code != 200:
        raise Exception(response.json())
    return [
        Metrics(
            ttft=metrics_dct["ttft"],
            itl=metrics_dct["itl"],
            input_cost=metrics_dct["input_cost"],
            output_cost=metrics_dct["output_cost"],
            measured_at=metrics_dct["measured_at"],
        )
        for metrics_dct in response.json()
    ]


def log_endpoint_metric(
    endpoint_name: str,
    *,
    metric_name: str,
    value: float,
    measured_at: Optional[Union[str, datetime.datetime]] = None,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Append speed or cost data to the standardized time-series benchmarks for a custom
    endpoint (only custom endpoints are publishable by end users).

    Args:
        endpoint_name: Name of the custom endpoint to append benchmark data for.

        metric_name: Name of the metric to submit. Allowed metrics are: “input_cost”,
        “output_cost”, “ttft”, “itl”.

        value: Value of the metric to submit.

        measured_at: The timestamp to associate with the submission. Defaults to current
        time if unspecified.

        api_key: If specified, unify API key to be used. Defaults to the value in the
        `UNIFY_KEY` environment variable.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    params = {
        "endpoint_name": endpoint_name,
        "metric_name": metric_name,
        "value": value,
        "measured_at": measured_at,
    }
    response = _requests.post(
        BASE_URL + "/endpoint-metrics",
        headers=headers,
        params=params,
    )
    if response.status_code != 200:
        raise Exception(response.json())
    return response.json()


def delete_endpoint_metrics(
    endpoint_name: str,
    *,
    timestamps: Optional[Union[datetime.datetime, List[datetime.datetime]]] = None,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    params = {
        "endpoint_name": endpoint_name,
        "timestamps": timestamps,
    }
    response = _requests.delete(
        BASE_URL + "/endpoint-metrics",
        headers=headers,
        params=params,
    )
    if response.status_code != 200:
        raise Exception(response.json())
    return response.json()
