class UnifyError(Exception):
    """Base class for all custom exceptions in the Unify application."""


class BadRequestError(UnifyError):
    """Exception raised for HTTP 400 Bad Request errors."""


class AuthenticationError(UnifyError):
    """Exception raised for HTTP 401 Unauthorized errors."""


class PermissionDeniedError(UnifyError):
    """Exception raised for HTTP 403 Forbidden errors."""


class NotFoundError(UnifyError):
    """Exception raised for HTTP 404 Not Found errors."""


class ConflictError(UnifyError):
    """Exception raised for HTTP 409 Conflict errors."""


class UnprocessableEntityError(UnifyError):
    """Exception raised for HTTP 422 Unprocessable Entity errors."""


class RateLimitError(UnifyError):
    """Exception raised for HTTP 429 Too Many Requests errors."""


class InternalServerError(UnifyError):
    """Exception raised for HTTP 500 Internal Server Error errors."""


status_error_map = {
    400: BadRequestError,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    422: UnprocessableEntityError,
    429: RateLimitError,
    500: InternalServerError,
}
