"""
Middleware for request handling, logging, and error tracking.
"""
import time
import uuid
from typing import Callable, Dict, List

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .logging import request_logger, get_logger

logger = get_logger("middleware")


class TraceIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add trace ID to all requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract trace ID
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
        request.state.trace_id = trace_id
        
        # Add trace ID to response headers
        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
        
        # Extract user ID if available (from JWT token)
        user_id = getattr(request.state, "user_id", None)
        
        # Log incoming request
        request_logger.log_request(
            request=request,
            trace_id=trace_id,
            user_id=user_id
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Log outgoing response
        request_logger.log_response(
            request=request,
            trace_id=trace_id,
            status_code=response.status_code,
            response_time=response_time,
            user_id=user_id
        )
        
        return response


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to track and log errors with enhanced context."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Add enhanced error context
            if not hasattr(exc, '_error_context'):
                exc._error_context = {
                    'request_path': str(request.url.path),
                    'request_method': request.method,
                    'client_host': request.client.host if request.client else None,
                    'user_agent': request.headers.get('user-agent'),
                    'content_type': request.headers.get('content-type'),
                    'trace_id': getattr(request.state, 'trace_id', None),
                    'user_id': getattr(request.state, 'user_id', None),
                    'request_size': request.headers.get('content-length'),
                    'referer': request.headers.get('referer'),
                    'accept': request.headers.get('accept'),
                    'query_params': dict(request.query_params),
                    'path_params': dict(request.path_params) if hasattr(request, 'path_params') else {}
                }
            
            # Log the error with context
            logger.error(
                f"Request failed: {type(exc).__name__} - {str(exc)}",
                extra={
                    "trace_id": getattr(request.state, 'trace_id', None),
                    "error_context": exc._error_context,
                    "exception_type": type(exc).__name__
                }
            )
            
            raise exc


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for basic rate limiting."""
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.client_requests: Dict[str, List[float]] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_old_entries(current_time)
        
        # Check rate limit
        if client_ip in self.client_requests:
            requests = self.client_requests[client_ip]
            recent_requests = [req_time for req_time in requests if current_time - req_time < 60]
            
            if len(recent_requests) >= self.calls_per_minute:
                logger.warning(
                    f"Rate limit exceeded for client {client_ip}",
                    extra={
                        "client_ip": client_ip,
                        "requests_count": len(recent_requests),
                        "limit": self.calls_per_minute,
                        "path": str(request.url.path),
                        "trace_id": getattr(request.state, 'trace_id', None)
                    }
                )
                
                from .exceptions import RateLimitException
                raise RateLimitException(
                    f"Rate limit exceeded. Maximum {self.calls_per_minute} requests per minute."
                )
            
            self.client_requests[client_ip] = recent_requests + [current_time]
        else:
            self.client_requests[client_ip] = [current_time]
        
        return await call_next(request)
    
    def _cleanup_old_entries(self, current_time: float):
        """Remove old request entries to prevent memory leaks."""
        for client_ip in list(self.client_requests.keys()):
            requests = self.client_requests[client_ip]
            recent_requests = [req_time for req_time in requests if current_time - req_time < 60]
            
            if recent_requests:
                self.client_requests[client_ip] = recent_requests
            else:
                del self.client_requests[client_ip]


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware to handle health check requests efficiently."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging and other processing for health check endpoints
        if request.url.path in ["/health", "/healthz", "/ping"]:
            return Response(content="OK", status_code=200)
        
        return await call_next(request)