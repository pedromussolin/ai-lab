"""Application-level exceptions."""

from typing import Any


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        error_code: str = "APP_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppException):
    def __init__(self, resource: str, resource_id: Any = None) -> None:
        msg = f"{resource} not found"
        if resource_id:
            msg = f"{resource} '{resource_id}' not found"
        super().__init__(msg, error_code="NOT_FOUND", status_code=404)


class ValidationError(AppException):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, error_code="VALIDATION_ERROR", status_code=422, details=details)


class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message, error_code="AUTHENTICATION_ERROR", status_code=401)


class AuthorizationError(AppException):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message, error_code="AUTHORIZATION_ERROR", status_code=403)


class ProviderError(AppException):
    def __init__(self, provider: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            f"Provider '{provider}' error: {message}",
            error_code="PROVIDER_ERROR",
            status_code=502,
            details=details,
        )


class RateLimitError(AppException):
    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(message, error_code="RATE_LIMIT", status_code=429)


class DocumentProcessingError(AppException):
    def __init__(self, filename: str, reason: str) -> None:
        super().__init__(
            f"Failed to process document '{filename}': {reason}",
            error_code="DOCUMENT_PROCESSING_ERROR",
            status_code=422,
        )


class GuardrailViolationError(AppException):
    def __init__(self, rule: str, message: str = "Content policy violation") -> None:
        super().__init__(
            message,
            error_code="GUARDRAIL_VIOLATION",
            status_code=422,
            details={"violated_rule": rule},
        )
