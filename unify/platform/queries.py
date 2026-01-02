import datetime
from typing import Dict, List, Optional, Union

from unify import BASE_URL
from unify.utils import http

from ..utils.helpers import _create_request_header


def log_query(
    *,
    endpoint: str,
    query_body: Dict,
    response_body: Optional[Dict] = None,
    tags: Optional[List[str]] = None,
    timestamp: Optional[Union[datetime.datetime, str]] = None,
    api_key: Optional[str] = None,
    consume_credits: bool = False,
):
    """
    Log a query (and optionally response) for a locally deployed (non-Unify-registered)
    model, with tagging (default None) and timestamp (default datetime.now() also
    optionally writeable.

    Args:
        endpoint: Endpoint to log query for.
        query_body: A dict containing the body of the request.
        response_body: An optional dict containing the response to the request.
        tags: Custom tags for later filtering.
        timestamp: A timestamp (if not set, will be the time of sending).
        api_key: If specified, unify API key to be used. Defaults to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A dictionary containing the response message if successful.

    Raises:
        requests.HTTPError: If the API request fails.
    """
    headers = _create_request_header(api_key)

    data = {
        "endpoint": endpoint,
        "query_body": query_body,
        "response_body": response_body,
        "tags": tags,
        "timestamp": timestamp,
        "consume_credits": consume_credits,
    }

    # Remove None values from params
    data = {k: v for k, v in data.items() if v is not None}

    url = f"{BASE_URL}/queries"

    response = http.post(url, headers=headers, json=data)
    if response.status_code != 200:
        raise Exception(response.json())

    return response.json()
