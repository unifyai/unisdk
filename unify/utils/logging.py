import requests
from typing import Optional, List, Any, Dict, Union

from unify import BASE_URL
from .helpers import _validate_api_key


def get_query_tags(api_key: Optional[str] = None) -> List[str]:
    """
    Get a list of available query tags.

    Args:
        api_key: If specified, unify API key to be used. Defaults
        to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A list of available query tags if successful, otherwise an empty list.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{BASE_URL}/tags"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return []


def get_query_history(
    tags: Optional[Union[str, List[str]]] = None,
    endpoints: Optional[Union[str, List[str]]] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get query history based on specified filters.

    Args:
        tags: Tags to filter for queries that are marked with these tags.
        endpoints: Optionally specify an endpoint, or a list of endpoints to filter for.
        start_time: Timestamp of the earliest query to aggregate. Format is `YYYY-MM-DD hh:mm:ss`.
        end_time: Timestamp of the latest query to aggregate. Format is `YYYY-MM-DD hh:mm:ss`.
        api_key: If specified, unify API key to be used. Defaults to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing the query history data.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    params = {}
    if tags:
        params["tags"] = tags if isinstance(tags, str) else ",".join(tags)
    if endpoints:
        params["endpoints"] = (
            endpoints if isinstance(endpoints, str) else ",".join(endpoints)
        )
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time

    url = f"{BASE_URL}/queries"
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def get_query_metrics(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    models: Optional[str] = None,
    providers: Optional[str] = None,
    interval: int = 300,
    secondary_user_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get query metrics for specified parameters.

    Args:
        start_time: Timestamp of the earliest query to aggregate. Format is `YYYY-MM-DD hh:mm:ss`.
        end_time: Timestamp of the latest query to aggregate. Format is `YYYY-MM-DD hh:mm:ss`.
        models: Models to fetch metrics from. Comma-separated string of model names.
        providers: Providers to fetch metrics from. Comma-separated string of provider names.
        interval: Number of seconds in the aggregation interval. Default is 300.
        secondary_user_id: Secondary user id to match the `user` attribute from `/chat/completions`.
        api_key: If specified, unify API key to be used. Defaults to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing the query metrics.
    """
    api_key = _validate_api_key(api_key)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    params = {
        "start_time": start_time,
        "end_time": end_time,
        "models": models,
        "providers": providers,
        "interval": interval,
        "secondary_user_id": secondary_user_id,
    }

    # Remove None values from params
    params = {k: v for k, v in params.items() if v is not None}

    url = f"{BASE_URL}/metrics"

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()
