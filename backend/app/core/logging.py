"""
Structured logging configuration with trace ID support.
"""
import json
import logging
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import Request
from pythonjsonlogger import jsonlogger


class TraceIDFilter(logging.Filter):
    """Filter to add trace ID to log records."""
    
    def filter(self, record):
        # Try to get trace_id from context or generate new one
        trace_id = getattr(record, 'trace_id', None)
        if not trace_id:
            trace_id = str(uuid.uuid4())
        record.trace_id = trace_id
        return True


class StructuredFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add trace_id if available
        if hasattr(record, 'trace_id'):
            log_record['trace_id'] = record.trace_id
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'path'):
            log_record['path'] = record.path
        if hasattr(record, 'method'):
            log_record['method'] = record.method
        if hasattr(record, 'ip_address'):
            log_record['ip_address'] = record.ip_address


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """Setup structured logging configuration."""
    
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if log_format.lower() == "json":
        # Use structured JSON logging
        formatter = StructuredFormatter(
            fmt='%(timestamp)s %(level)s %(logger)s %(trace_id)s %(message)s'
        )
    else:
        # Use standard text logging
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(trace_id)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    
    # Add trace ID filter
    trace_filter = TraceIDFilter()
    console_handler.addFilter(trace_filter)
    
    # Configure root logger
    root_logger.addHandler(console_handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Configure specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


class RequestLogger:
    """Logger for HTTP requests with context."""
    
    def __init__(self):
        self.logger = logging.getLogger("pafar.requests")
    
    def log_request(
        self,
        request: Request,
        trace_id: str,
        user_id: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """Log incoming request."""
        extra_data = {
            'trace_id': trace_id,
            'path': str(request.url),
            'method': request.method,
            'ip_address': request.client.host if request.client else None,
            'user_agent': request.headers.get('user-agent'),
            'request_id': id(request)
        }
        
        if user_id:
            extra_data['user_id'] = user_id
        
        if additional_data:
            extra_data.update(additional_data)
        
        self.logger.info(
            f"Request: {request.method} {request.url.path}",
            extra=extra_data
        )
    
    def log_response(
        self,
        request: Request,
        trace_id: str,
        status_code: int,
        response_time: float,
        user_id: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """Log outgoing response."""
        extra_data = {
            'trace_id': trace_id,
            'path': str(request.url),
            'method': request.method,
            'status_code': status_code,
            'response_time_ms': round(response_time * 1000, 2),
            'request_id': id(request)
        }
        
        if user_id:
            extra_data['user_id'] = user_id
        
        if additional_data:
            extra_data.update(additional_data)
        
        log_level = logging.ERROR if status_code >= 500 else logging.WARNING if status_code >= 400 else logging.INFO
        
        self.logger.log(
            log_level,
            f"Response: {request.method} {request.url.path} - {status_code}",
            extra=extra_data
        )


class BusinessLogger:
    """Logger for business operations."""
    
    def __init__(self):
        self.logger = logging.getLogger("pafar.business")
    
    def log_booking_created(self, booking_id: str, user_id: str, trip_id: str, trace_id: str):
        """Log booking creation."""
        self.logger.info(
            f"Booking created: {booking_id}",
            extra={
                'trace_id': trace_id,
                'user_id': user_id,
                'booking_id': booking_id,
                'trip_id': trip_id,
                'operation': 'booking_created'
            }
        )
    
    def log_payment_processed(self, payment_id: str, booking_id: str, amount: float, trace_id: str):
        """Log payment processing."""
        self.logger.info(
            f"Payment processed: {payment_id}",
            extra={
                'trace_id': trace_id,
                'payment_id': payment_id,
                'booking_id': booking_id,
                'amount': amount,
                'operation': 'payment_processed'
            }
        )
    
    def log_trip_status_update(self, trip_id: str, old_status: str, new_status: str, trace_id: str):
        """Log trip status updates."""
        self.logger.info(
            f"Trip status updated: {trip_id} from {old_status} to {new_status}",
            extra={
                'trace_id': trace_id,
                'trip_id': trip_id,
                'old_status': old_status,
                'new_status': new_status,
                'operation': 'trip_status_update'
            }
        )
    
    def log_external_service_call(
        self,
        service: str,
        operation: str,
        success: bool,
        response_time: float,
        trace_id: str,
        error_message: Optional[str] = None
    ):
        """Log external service calls."""
        log_level = logging.INFO if success else logging.ERROR
        message = f"External service call: {service}.{operation} - {'SUCCESS' if success else 'FAILED'}"
        
        extra_data = {
            'trace_id': trace_id,
            'service': service,
            'operation': operation,
            'success': success,
            'response_time_ms': round(response_time * 1000, 2)
        }
        
        if error_message:
            extra_data['error_message'] = error_message
        
        self.logger.log(log_level, message, extra=extra_data)


# Global logger instances
request_logger = RequestLogger()
business_logger = BusinessLogger()


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(f"pafar.{name}")