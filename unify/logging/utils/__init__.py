import requests


class RequestError(Exception):
    def __init__(self, response: requests.Response):
        req = response.request
        message = (
            f"{req.method} {req.url} failed with status code {response.status_code}. "
            f"Request body: {req.body}, Response: {response.text}"
        )
        super().__init__(message)
        self.response = response


def _check_response(response: requests.Response):
    if not response.ok:
        raise RequestError(response)
