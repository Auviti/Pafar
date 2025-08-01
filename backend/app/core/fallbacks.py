"""
Fallback mechanisms for third-party service failures.
"""
import asyncio
import logging
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from functools import wraps
from datetime import datetime, timedelta

from .exceptions import ExternalServiceException
from .logging import business_logger

T = TypeVar('T')

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit breaker pattern implementation for external services."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if self._should_attempt_reset():
                    self.state = "HALF_OPEN"
                else:
                    raise ExternalServiceException(
                        service=func.__name__,
                        message="Circuit breaker is OPEN"
                    )
            
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise e
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
    
    def _on_success(self):
        """Reset circuit breaker on successful call."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failure and potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class RetryMechanism:
    """Retry mechanism with exponential backoff."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(self.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == self.max_retries:
                        logger.error(f"Max retries exceeded for {func.__name__}: {str(e)}")
                        raise e
                    
                    delay = self._calculate_delay(attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {delay}s: {str(e)}")
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        return wrapper
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and optional jitter."""
        delay = min(self.base_delay * (self.exponential_base ** attempt), self.max_delay)
        
        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
        
        return delay


class FallbackService:
    """Service for managing fallback mechanisms."""
    
    def __init__(self):
        self.fallback_data: Dict[str, Any] = {}
        self.service_status: Dict[str, Dict[str, Any]] = {}
    
    def register_fallback_data(self, service: str, data: Any):
        """Register fallback data for a service."""
        self.fallback_data[service] = data
        logger.info(f"Registered fallback data for service: {service}")
    
    def get_fallback_data(self, service: str) -> Optional[Any]:
        """Get fallback data for a service."""
        return self.fallback_data.get(service)
    
    def update_service_status(self, service: str, status: str, error: Optional[str] = None):
        """Update service status."""
        self.service_status[service] = {
            "status": status,
            "last_updated": datetime.now(),
            "error": error
        }
    
    def get_service_status(self, service: str) -> Dict[str, Any]:
        """Get service status."""
        return self.service_status.get(service, {"status": "unknown"})
    
    def is_service_healthy(self, service: str) -> bool:
        """Check if service is healthy."""
        status = self.get_service_status(service)
        return status.get("status") == "healthy"


# Global fallback service instance
fallback_service = FallbackService()


# Decorators for common fallback patterns
def with_circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    service_name: str = None
):
    """Decorator to add circuit breaker to a function."""
    def decorator(func: Callable) -> Callable:
        circuit_breaker = CircuitBreaker(failure_threshold, recovery_timeout)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await circuit_breaker(func)(*args, **kwargs)
                if service_name:
                    fallback_service.update_service_status(service_name, "healthy")
                return result
            except Exception as e:
                if service_name:
                    fallback_service.update_service_status(service_name, "unhealthy", str(e))
                raise e
        
        return wrapper
    return decorator


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    service_name: str = None
):
    """Decorator to add retry mechanism to a function."""
    def decorator(func: Callable) -> Callable:
        retry_mechanism = RetryMechanism(max_retries, base_delay)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await retry_mechanism(func)(*args, **kwargs)
                if service_name:
                    fallback_service.update_service_status(service_name, "healthy")
                return result
            except Exception as e:
                if service_name:
                    fallback_service.update_service_status(service_name, "unhealthy", str(e))
                raise e
        
        return wrapper
    return decorator


def with_fallback(fallback_data: Any = None, service_name: str = None):
    """Decorator to provide fallback data when service fails."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                if service_name:
                    fallback_service.update_service_status(service_name, "healthy")
                return result
            except Exception as e:
                logger.warning(f"Service {func.__name__} failed, using fallback: {str(e)}")
                
                if service_name:
                    fallback_service.update_service_status(service_name, "unhealthy", str(e))
                    registered_fallback = fallback_service.get_fallback_data(service_name)
                    if registered_fallback is not None:
                        return registered_fallback
                
                if fallback_data is not None:
                    return fallback_data
                
                # If no fallback available, re-raise the exception
                raise e
        
        return wrapper
    return decorator


# Health check endpoint data
@with_fallback(fallback_data={"status": "degraded", "services": {}})
async def get_service_health_status() -> Dict[str, Any]:
    """Get overall service health status."""
    services = {}
    overall_status = "healthy"
    
    for service, status_info in fallback_service.service_status.items():
        services[service] = {
            "status": status_info["status"],
            "last_updated": status_info["last_updated"].isoformat(),
            "error": status_info.get("error")
        }
        
        if status_info["status"] != "healthy":
            overall_status = "degraded"
    
    return {
        "status": overall_status,
        "services": services,
        "timestamp": datetime.now().isoformat()
    }