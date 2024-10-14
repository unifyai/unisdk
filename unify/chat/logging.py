import datetime
from typing import List, Optional

import unify

from ..utils.helpers import _validate_api_key


def with_logging(
    model_fn: Optional[callable] = None,
    *,
    endpoint: str,
    tags: Optional[List[str]] = None,
    timestamp: Optional[datetime.datetime] = None,
    log_query_body: bool = True,
    log_response_body: bool = True,
    api_key: Optional[str] = None,
):
    """
    Wrap a local model callable with logging of the queries.

    Args:
        model_fn: The model callable to wrap logging around.
        endpoint: The endpoint name to give to this local callable.
        tags: Tags for later filtering.
        timestamp: A timestamp (if not set, will be the time of sending).
        log_query_body: Whether or not to log the query body.
        log_response_body: Whether or not to log the response body.
        api_key: If specified, unify API key to be used. Defaults to the value in the `UNIFY_KEY` environment variable.

    Returns:
        A new callable, but with logging added every time the function is called.

    Raises:
        requests.HTTPError: If the API request fails.
    """
    _tags = tags
    _timestamp = timestamp
    _log_query_body = log_query_body
    _log_response_body = log_response_body
    api_key = _validate_api_key(api_key)

    # noinspection PyShadowingNames
    def model_fn_w_logging(
        *args,
        tags: Optional[List[str]] = None,
        timestamp: Optional[datetime.datetime] = None,
        log_query_body: bool = True,
        log_response_body: bool = True,
        **kwargs,
    ):
        if len(args) != 0:
            raise Exception(
                "When logging queries for a local model, all arguments to "
                "the model callable must be provided as keyword arguments. "
                "Positional arguments are not supported. This is so the "
                "query body dict can be fully populated with keys for each "
                "entry.",
            )
        query_body = kwargs
        response = model_fn(**query_body)
        if not isinstance(response, dict):
            response = {"response": response}
        kw = dict(
            endpoint=endpoint,
            query_body=query_body,
            response_body=response,
            tags=tags,
            timestamp=timestamp,
            api_key=api_key,
        )
        if log_query_body:
            if not log_response_body:
                del kw["response_body"]
            unify.log_query(**kw)
        return response

    return model_fn_w_logging
