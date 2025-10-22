"""
Custom HTTP exceptions for the TURN application.
"""
from typing import Any, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.core.error_codes import ErrorCode, ERROR_MESSAGES


class ErrorDetail(BaseModel):
    """Error detail model."""
    code: str
    message: str
    field: Optional[str] = None


class CustomHTTPException(HTTPException):
    """
    Custom HTTP exception with structured error response.
    """
    
    def __init__(
        self,
        status_code: int,
        error_code: ErrorCode,
        detail: Optional[str] = None,
        field: Optional[str] = None,
        headers: Optional[dict] = None
    ):
        self.error_code = error_code
        self.field = field
        
        # Use provided detail or default from error code
        if detail is None:
            detail = ERROR_MESSAGES.get(error_code, "Unknown error")
        
        super().__init__(
            status_code=status_code,
            detail={
                "error": {
                    "code": error_code.value,
                    "message": detail,
                    "field": field
                }
            },
            headers=headers
        )


# Common exception shortcuts
class AuthenticationError(CustomHTTPException):
    """Authentication related errors."""
    
    def __init__(self, error_code: ErrorCode = ErrorCode.INVALID_CREDENTIALS, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(CustomHTTPException):
    """Authorization related errors."""
    
    def __init__(self, error_code: ErrorCode = ErrorCode.INSUFFICIENT_PERMISSIONS, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code,
            detail=detail
        )


class NotFoundError(CustomHTTPException):
    """Resource not found errors."""
    
    def __init__(self, error_code: ErrorCode = ErrorCode.RESOURCE_NOT_FOUND, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code,
            detail=detail
        )


class ValidationError(CustomHTTPException):
    """Validation errors."""
    
    def __init__(self, error_code: ErrorCode = ErrorCode.VALIDATION_ERROR, detail: Optional[str] = None, field: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=error_code,
            detail=detail,
            field=field
        )


class ConflictError(CustomHTTPException):
    """Resource conflict errors."""
    
    def __init__(self, error_code: ErrorCode, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code=error_code,
            detail=detail
        )


class ServiceUnavailableError(CustomHTTPException):
    """Service unavailable errors."""
    
    def __init__(self, error_code: ErrorCode, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code=error_code,
            detail=detail
        )