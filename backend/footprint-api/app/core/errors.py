from enum import StrEnum

from starlette import status


class ErrorCode(StrEnum):
    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_API_KEY = "INVALID_API_KEY"
    API_KEY_EXPIRED = "API_KEY_EXPIRED"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    PROVIDER_NOT_FOUND = "PROVIDER_NOT_FOUND"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    MODEL_NOT_SUPPORTED = "MODEL_NOT_SUPPORTED"
    INVALID_WORKLOAD = "INVALID_WORKLOAD"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    METHODOLOGY_UNAVAILABLE = "METHODOLOGY_UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"


_STATUS_BY_CODE: dict[ErrorCode, int] = {
    ErrorCode.INVALID_REQUEST: status.HTTP_400_BAD_REQUEST,
    ErrorCode.INVALID_API_KEY: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.API_KEY_EXPIRED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.UNAUTHORIZED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.FORBIDDEN: status.HTTP_403_FORBIDDEN,
    ErrorCode.PROVIDER_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.MODEL_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.MODEL_NOT_SUPPORTED: status.HTTP_422_UNPROCESSABLE_CONTENT,
    ErrorCode.INVALID_WORKLOAD: status.HTTP_422_UNPROCESSABLE_CONTENT,
    ErrorCode.MISSING_PARAMETER: status.HTTP_400_BAD_REQUEST,
    ErrorCode.METHODOLOGY_UNAVAILABLE: status.HTTP_200_OK,
    ErrorCode.RATE_LIMITED: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


class AppError(Exception):
    """Base application error mapped to the API error contract (FRD section 25)."""

    def __init__(self, code: ErrorCode, message: str, status_code: int | None = None) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code or _STATUS_BY_CODE.get(
            code, status.HTTP_400_BAD_REQUEST
        )
        super().__init__(message)


class InvalidRequestError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(ErrorCode.INVALID_REQUEST, message)


class MissingParameterError(AppError):
    def __init__(self, parameter: str) -> None:
        super().__init__(ErrorCode.MISSING_PARAMETER, f"Missing required parameter: {parameter}")


class InvalidWorkloadError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(ErrorCode.INVALID_WORKLOAD, message)


class InvalidApiKeyError(AppError):
    def __init__(self, message: str = "The provided API key is invalid or revoked.") -> None:
        super().__init__(ErrorCode.INVALID_API_KEY, message)


class ApiKeyExpiredError(AppError):
    def __init__(self, message: str = "The provided API key has expired.") -> None:
        super().__init__(ErrorCode.API_KEY_EXPIRED, message)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication is required for this endpoint.") -> None:
        super().__init__(ErrorCode.UNAUTHORIZED, message)


class ForbiddenError(AppError):
    def __init__(self, message: str = "You do not have access to this resource.") -> None:
        super().__init__(ErrorCode.FORBIDDEN, message)


class ProviderNotFoundError(AppError):
    def __init__(self, provider: str) -> None:
        super().__init__(ErrorCode.PROVIDER_NOT_FOUND, f"Provider '{provider}' was not found.")


class ModelNotFoundError(AppError):
    def __init__(self, provider: str, model: str) -> None:
        super().__init__(
            ErrorCode.MODEL_NOT_FOUND,
            f"Model '{model}' was not found for provider '{provider}'.",
        )


class ModelNotSupportedError(AppError):
    def __init__(self, message: str = "The requested model is not currently supported.") -> None:
        super().__init__(ErrorCode.MODEL_NOT_SUPPORTED, message)


class RateLimitedError(AppError):
    def __init__(self, message: str = "Rate limit exceeded.") -> None:
        super().__init__(ErrorCode.RATE_LIMITED, message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found.") -> None:
        super().__init__(ErrorCode.NOT_FOUND, message)
