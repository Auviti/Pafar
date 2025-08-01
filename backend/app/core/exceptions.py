"""
Custom exceptions and global exception handlers for the Pafar application.
"""
import logging
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .monitoring import record_exception_error
from .logging import get_logger

logger = get_logger("exceptions")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: Dict[str, Any]
    trace_id: str
    timestamp: str
    path: str


class PafarException(Exception):
    """Base exception class for Pafar application."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(PafarException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field": field, **(details or {})}
        )


class AuthenticationException(PafarException):
    """Exception for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationException(PafarException):
    """Exception for authorization errors."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN
        )


class ResourceNotFoundException(PafarException):
    """Exception for resource not found errors."""
    
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message += f" with identifier: {identifier}"
        
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": identifier}
        )


class BusinessLogicException(PafarException):
    """Exception for business logic violations."""
    
    def __init__(self, message: str, error_code: str = "BUSINESS_LOGIC_ERROR"):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_409_CONFLICT
        )


class BookingNotAvailableException(BusinessLogicException):
    """Exception for booking availability issues."""
    
    def __init__(self, trip_id: str, seats: list = None):
        message = f"Booking not available for trip {trip_id}"
        if seats:
            message += f" for seats: {seats}"
        
        super().__init__(
            message=message,
            error_code="BOOKING_NOT_AVAILABLE"
        )


class PaymentException(PafarException):
    """Exception for payment processing errors."""
    
    def __init__(self, message: str, payment_error_code: str = None):
        super().__init__(
            message=message,
            error_code="PAYMENT_ERROR",
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            details={"payment_error_code": payment_error_code}
        )


class ExternalServiceException(PafarException):
    """Exception for external service failures."""
    
    def __init__(self, service: str, message: str = None):
        message = message or f"External service {service} is unavailable"
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service}
        )


class RateLimitException(PafarException):
    """Exception for rate limiting."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


def get_trace_id(request: Request) -> str:
    """Get or generate trace ID for request tracking."""
    trace_id = getattr(request.state, "trace_id", None)
    if not trace_id:
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id
    return trace_id


async def pafar_exception_handler(request: Request, exc: PafarException) -> JSONResponse:
    """Handle custom Pafar exceptions."""
    trace_id = get_trace_id(request)
    user_id = getattr(request.state, "user_id", None)
    
    logger.error(
        f"PafarException: {exc.error_code} - {exc.message}",
        extra={
            "trace_id": trace_id,
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": str(request.url),
            "method": request.method
        }
    )
    
    # Record error for monitoring
    await record_exception_error(
        exception=exc,
        trace_id=trace_id,
        service="api",
        endpoint=str(request.url.path),
        user_id=user_id,
        metadata={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "method": request.method
        }
    )
    
    error_response = ErrorResponse(
        error={
            "code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        },
        trace_id=trace_id,
        timestamp=datetime.utcnow().isoformat(),
        path=str(request.url)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    trace_id = get_trace_id(request)
    
    logger.warning(
        f"HTTPException: {exc.status_code} - {exc.detail}",
        extra={
            "trace_id": trace_id,
            "status_code": exc.status_code,
            "path": str(request.url),
            "method": request.method
        }
    )
    
    error_response = ErrorResponse(
        error={
            "code": "HTTP_ERROR",
            "message": exc.detail,
            "details": {}
        },
        trace_id=trace_id,
        timestamp=datetime.utcnow().isoformat(),
        path=str(request.url)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    trace_id = get_trace_id(request)
    user_id = getattr(request.state, "user_id", None)
    
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "trace_id": trace_id,
            "exception_type": type(exc).__name__,
            "path": str(request.url),
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )
    
    # Record error for monitoring
    await record_exception_error(
        exception=exc,
        trace_id=trace_id,
        service="api",
        endpoint=str(request.url.path),
        user_id=user_id,
        metadata={
            "exception_type": type(exc).__name__,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )
    
    error_response = ErrorResponse(
        error={
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": {}
        },
        trace_id=trace_id,
        timestamp=datetime.utcnow().isoformat(),
        path=str(request.url)
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.dict()
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation exceptions."""
    trace_id = get_trace_id(request)
    user_id = getattr(request.state, "user_id", None)
    
    # Extract validation errors
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error.get("loc", [])),
            "message": error.get("msg", ""),
            "type": error.get("type", ""),
            "input": error.get("input")
        })
    
    logger.warning(
        f"Validation error: {len(errors)} field(s) failed validation",
        extra={
            "trace_id": trace_id,
            "path": str(request.url),
            "method": request.method,
            "validation_errors": errors,
            "user_id": user_id
        }
    )
    
    # Record validation error for monitoring
    await record_exception_error(
        exception=exc,
        trace_id=trace_id,
        service="api",
        endpoint=str(request.url.path),
        user_id=user_id,
        metadata={
            "validation_errors": errors,
            "method": request.method,
            "error_count": len(errors)
        }
    )
    
    error_response = ErrorResponse(
        error={
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {"validation_errors": errors}
        },
        trace_id=trace_id,
        timestamp=datetime.utcnow().isoformat(),
        path=str(request.url)
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.dict()
    )


async def request_validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle FastAPI RequestValidationError."""
    trace_id = get_trace_id(request)
    user_id = getattr(request.state, "user_id", None)
    
    # Extract validation errors from RequestValidationError
    errors = []
    if hasattr(exc, 'errors'):
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(x) for x in error.get("loc", [])),
                "message": error.get("msg", ""),
                "type": error.get("type", ""),
                "input": error.get("input")
            })
    
    logger.warning(
        f"Request validation error: {len(errors)} field(s) failed validation",
        extra={
            "trace_id": trace_id,
            "path": str(request.url),
            "method": request.method,
            "validation_errors": errors,
            "user_id": user_id
        }
    )
    
    error_response = ErrorResponse(
        error={
            "code": "REQUEST_VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {"validation_errors": errors}
        },
        trace_id=trace_id,
        timestamp=datetime.utcnow().isoformat(),
        path=str(request.url)
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.dict()
    )


async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle Starlette HTTP exceptions."""
    trace_id = get_trace_id(request)
    user_id = getattr(request.state, "user_id", None)
    
    logger.warning(
        f"Starlette HTTP exception: {exc.status_code} - {exc.detail}",
        extra={
            "trace_id": trace_id,
            "status_code": exc.status_code,
            "path": str(request.url),
            "method": request.method,
            "user_id": user_id
        }
    )
    
    error_response = ErrorResponse(
        error={
            "code": "HTTP_ERROR",
            "message": exc.detail,
            "details": {"status_code": exc.status_code}
        },
        trace_id=trace_id,
        timestamp=datetime.utcnow().isoformat(),
        path=str(request.url)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )