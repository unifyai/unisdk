"""
Storage utilities for accessing GCS objects through Orchestra.

These functions provide a clean interface for retrieving content from
Google Cloud Storage without requiring direct GCS credentials.
"""

import base64
from typing import Optional

from unisdk import BASE_URL
from unisdk.utils import http
from unisdk.utils.helpers import _create_request_header, _validate_api_key


def get_signed_url(
    gcs_uri: str,
    *,
    expiration_minutes: int = 60,
    api_key: Optional[str] = None,
) -> str:
    """
    Generate a signed URL for a GCS object.

    Creates a time-limited, publicly accessible URL for downloading
    a Google Cloud Storage object without requiring authentication.

    Args:
        gcs_uri: The GCS URI of the object (e.g., "gs://bucket-name/path/to/object").

        expiration_minutes: How long the signed URL should remain valid, in minutes.
            Must be between 1 and 10080 (7 days). Defaults to 60 minutes.

        api_key: If specified, unify API key to be used. Defaults to the value
            in the `UNIFY_KEY` environment variable.

    Returns:
        A signed URL string that can be used to download the object via HTTP GET.

    Raises:
        RequestError: If the request fails (e.g., object not found, invalid URI).

    Example:
        >>> import unisdk
        >>> url = unisdk.get_signed_url("gs://my-bucket/images/photo.jpg")
        >>> # Use the URL to download the image
        >>> import requests
        >>> response = requests.get(url)
    """
    api_key = _validate_api_key(api_key)
    headers = _create_request_header(api_key)

    body = {
        "gcs_uri": gcs_uri,
        "expiration_minutes": expiration_minutes,
    }

    response = http.post(
        f"{BASE_URL}/storage/signed-url",
        headers=headers,
        json=body,
    )

    return response.json()["signed_url"]


def download_object(
    gcs_uri: str,
    *,
    api_key: Optional[str] = None,
) -> bytes:
    """
    Download a GCS object's content as bytes.

    Retrieves the content of a Google Cloud Storage object and returns
    it as raw bytes.

    Args:
        gcs_uri: The GCS URI of the object (e.g., "gs://bucket-name/path/to/object").

        api_key: If specified, unify API key to be used. Defaults to the value
            in the `UNIFY_KEY` environment variable.

    Returns:
        The raw bytes content of the object.

    Raises:
        RequestError: If the request fails (e.g., object not found, invalid URI).

    Example:
        >>> import unisdk
        >>> content = unisdk.download_object("gs://my-bucket/data/file.txt")
        >>> text = content.decode("utf-8")
        >>> print(text)
    """
    api_key = _validate_api_key(api_key)
    headers = _create_request_header(api_key)

    body = {
        "gcs_uri": gcs_uri,
    }

    response = http.post(
        f"{BASE_URL}/storage/download",
        headers=headers,
        json=body,
    )

    resp_json = response.json()
    content_base64 = resp_json["content_base64"]

    return base64.b64decode(content_base64)
