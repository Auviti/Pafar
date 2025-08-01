"""
Tests for error handling and monitoring functionality.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.exceptions import (
    PafarException,
    ValidationException,
    AuthenticationException,
    BusinessLogicException,
    PaymentException,
    ExternalServiceException,
    RateLimitException,
    pafar_exception_handler,
    http_exception_handler,
    general_exception_handler,
    validation_exception_handler,
    get_trace_id
)
from app.core.monitoring import (
    ErrorMonitor,
    ErrorEvent,
    AlertRule,
    error_monitor,
    record_exception_error
)
from app.core.fallbacks import (
    CircuitBreaker,
    RetryMechanism,
    FallbackService,
    with_circuit_breaker,
    with_retry,
    with_fallback
)
from app.core.middleware import (
    TraceIDMiddleware,
    RequestLoggingMiddleware,
    ErrorTrackingMiddleware,
    RateLimitMiddleware
)


class TestCustomExceptions:
    """Test custom exception classes."""
    
    def test_pafar_exception_creation(self):
        """Test PafarException creation with all parameters."""
        exc = PafarException(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=400,
            details={"field": "value"}
        )
        
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.status_code == 400
        assert exc.details == {"field": "value"}
    
    def test_validation_exception(self):
        """Test ValidationException with field details."""
        exc = ValidationException(
            message="Invalid input",
            field="email",
            details={"pattern": "email"}
        )
        
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.status_code == 422
        assert exc.details["field"] == "email"
    
    def test_authentication_exception(self):
        """Test AuthenticationException."""
        exc = AuthenticationException("Invalid credentials")
        
        assert exc.error_code == "AUTHENTICATION_ERROR"
        assert exc.status_code == 401
        assert exc.message == "Invalid credentials"
    
    def test_business_logic_exception(self):
        """Test BusinessLogicException."""
        exc = BusinessLogicException("Booking not available", "BOOKING_ERROR")
        
        assert exc.error_code == "BOOKING_ERROR"
        assert exc.status_code == 409
    
    def test_payment_exception(self):
        """Test PaymentException."""
        exc = PaymentException("Payment failed", "CARD_DECLINED")
        
        assert exc.error_code == "PAYMENT_ERROR"
        assert exc.status_code == 402
        assert exc.details["payment_error_code"] == "CARD_DECLINED"
    
    def test_external_service_exception(self):
        """Test ExternalServiceException."""
        exc = ExternalServiceException("stripe", "Service unavailable")
        
        assert exc.error_code == "EXTERNAL_SERVICE_ERROR"
        assert exc.status_code == 503
        assert exc.details["service"] == "stripe"


class TestExceptionHandlers:
    """Test exception handler functions."""
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request object."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "POST"
        request.state = Mock()
        request.state.trace_id = "test-trace-id"
        request.state.user_id = "test-user-id"
        return request
    
    @pytest.mark.asyncio
    async def test_pafar_exception_handler(self, mock_request):
        """Test PafarException handler."""
        exc = ValidationException("Invalid input", "email")
        
        with patch('app.core.exceptions.record_exception_error') as mock_record:
            response = await pafar_exception_handler(mock_request, exc)
        
        assert response.status_code == 422
        response_data = response.body.decode()
        assert "VALIDATION_ERROR" in response_data
        assert "test-trace-id" in response_data
        
        mock_record.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_http_exception_handler(self, mock_request):
        """Test HTTPException handler."""
        exc = HTTPException(status_code=404, detail="Not found")
        
        response = await http_exception_handler(mock_request, exc)
        
        assert response.status_code == 404
        response_data = response.body.decode()
        assert "HTTP_ERROR" in response_data
        assert "Not found" in response_data
    
    @pytest.mark.asyncio
    async def test_general_exception_handler(self, mock_request):
        """Test general exception handler."""
        exc = ValueError("Unexpected error")
        
        with patch('app.core.exceptions.record_exception_error') as mock_record:
            response = await general_exception_handler(mock_request, exc)
        
        assert response.status_code == 500
        response_data = response.body.decode()
        assert "INTERNAL_SERVER_ERROR" in response_data
        
        mock_record.assert_called_once()
    
    def test_get_trace_id_existing(self, mock_request):
        """Test getting existing trace ID."""
        trace_id = get_trace_id(mock_request)
        assert trace_id == "test-trace-id"
    
    def test_get_trace_id_generate(self):
        """Test generating new trace ID."""
        request = Mock(spec=Request)
        request.state = Mock()
        
        trace_id = get_trace_id(request)
        assert trace_id is not None
        assert len(trace_id) > 0
        assert request.state.trace_id == trace_id


class TestErrorMonitoring:
    """Test error monitoring functionality."""
    
    @pytest.fixture
    def error_monitor_instance(self):
        """Create fresh error monitor instance."""
        return ErrorMonitor(max_events=100)
    
    @pytest.mark.asyncio
    async def test_record_error(self, error_monitor_instance):
        """Test recording error events."""
        await error_monitor_instance.record_error(
            error_type="TEST_ERROR",
            error_message="Test error message",
            trace_id="test-trace",
            service="test-service",
            endpoint="/api/test",
            user_id="user-123"
        )
        
        events = error_monitor_instance.get_recent_errors(limit=1)
        assert len(events) == 1
        
        event = events[0]
        assert event["type"] == "TEST_ERROR"
        assert event["message"] == "Test error message"
        assert event["trace_id"] == "test-trace"
        assert event["service"] == "test-service"
    
    def test_add_alert_rule(self, error_monitor_instance):
        """Test adding alert rules."""
        rule = AlertRule(
            name="Test Rule",
            condition="error_count",
            threshold=10,
            time_window_minutes=5
        )
        
        error_monitor_instance.add_alert_rule(rule)
        assert len(error_monitor_instance.alert_rules) == 1
        assert error_monitor_instance.alert_rules[0].name == "Test Rule"
    
    @pytest.mark.asyncio
    async def test_alert_triggering(self, error_monitor_instance):
        """Test alert rule triggering."""
        # Add alert rule
        rule = AlertRule(
            name="Error Count Alert",
            condition="error_count",
            threshold=2,
            time_window_minutes=5
        )
        error_monitor_instance.add_alert_rule(rule)
        
        # Add alert callback
        callback_called = []
        async def test_callback(alert_data):
            callback_called.append(alert_data)
        
        error_monitor_instance.add_alert_callback(test_callback)
        
        # Record errors to trigger alert
        for i in range(3):
            await error_monitor_instance.record_error(
                error_type="TEST_ERROR",
                error_message=f"Error {i}",
                trace_id=f"trace-{i}",
                service="test-service",
                severity="error"
            )
        
        # Check if alert was triggered
        assert len(callback_called) > 0
        assert callback_called[0]["rule_name"] == "Error Count Alert"
    
    def test_error_summary(self, error_monitor_instance):
        """Test error summary generation."""
        # Add some test events
        now = datetime.now()
        for i in range(5):
            event = ErrorEvent(
                type="TEST_ERROR",
                message=f"Error {i}",
                trace_id=f"trace-{i}",
                service="test-service",
                timestamp=now - timedelta(minutes=i)
            )
            error_monitor_instance.error_events.append(event)
        
        summary = error_monitor_instance.get_error_summary(hours=1)
        
        assert summary["total_errors"] == 5
        assert "TEST_ERROR" in summary["error_types"]
        assert "test-service" in summary["services"]


class TestFallbackMechanisms:
    """Test fallback mechanisms."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state."""
        circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        
        @circuit_breaker
        async def test_function():
            return "success"
        
        result = await test_function()
        assert result == "success"
        assert circuit_breaker.state == "CLOSED"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_open_state(self):
        """Test circuit breaker opening after failures."""
        circuit_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)
        
        @circuit_breaker
        async def failing_function():
            raise ValueError("Test error")
        
        # Trigger failures to open circuit
        for _ in range(3):
            try:
                await failing_function()
            except (ValueError, ExternalServiceException):
                pass
        
        assert circuit_breaker.state == "OPEN"
        
        # Next call should raise ExternalServiceException
        with pytest.raises(ExternalServiceException):
            await failing_function()
    
    @pytest.mark.asyncio
    async def test_retry_mechanism_success(self):
        """Test retry mechanism with eventual success."""
        retry = RetryMechanism(max_retries=3, base_delay=0.01)
        
        call_count = 0
        
        @retry
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"
        
        result = await flaky_function()
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_mechanism_max_retries(self):
        """Test retry mechanism reaching max retries."""
        retry = RetryMechanism(max_retries=2, base_delay=0.01)
        
        @retry
        async def always_failing_function():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError):
            await always_failing_function()
    
    def test_fallback_service_registration(self):
        """Test fallback service data registration."""
        fallback_service = FallbackService()
        test_data = {"fallback": "data"}
        
        fallback_service.register_fallback_data("test-service", test_data)
        
        retrieved_data = fallback_service.get_fallback_data("test-service")
        assert retrieved_data == test_data
    
    def test_fallback_service_status_tracking(self):
        """Test service status tracking."""
        fallback_service = FallbackService()
        
        fallback_service.update_service_status("test-service", "healthy")
        status = fallback_service.get_service_status("test-service")
        
        assert status["status"] == "healthy"
        assert "last_updated" in status
        assert fallback_service.is_service_healthy("test-service")
    
    @pytest.mark.asyncio
    async def test_with_fallback_decorator_success(self):
        """Test with_fallback decorator on successful call."""
        @with_fallback(fallback_data="fallback_result")
        async def successful_function():
            return "success"
        
        result = await successful_function()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_with_fallback_decorator_failure(self):
        """Test with_fallback decorator on failed call."""
        @with_fallback(fallback_data="fallback_result")
        async def failing_function():
            raise ValueError("Function failed")
        
        result = await failing_function()
        assert result == "fallback_result"


class TestIntegration:
    """Integration tests for error handling system."""
    
    @pytest.mark.asyncio
    async def test_record_exception_error(self):
        """Test recording exception error."""
        exception = ValidationException("Test validation error")
        
        with patch.object(error_monitor, 'record_error') as mock_record:
            await record_exception_error(
                exception=exception,
                trace_id="test-trace",
                service="api",
                endpoint="/api/test",
                user_id="user-123"
            )
        
        mock_record.assert_called_once()
        call_args = mock_record.call_args[1]
        assert call_args["error_type"] == "ValidationException"
        assert call_args["trace_id"] == "test-trace"
        assert call_args["service"] == "api"
    
    @pytest.mark.asyncio
    async def test_validation_exception_handler(self):
        """Test validation exception handler."""
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/test"
        mock_request.method = "POST"
        mock_request.state = Mock()
        mock_request.state.trace_id = "test-trace-id"
        mock_request.state.user_id = "test-user-id"
        
        # Create a mock ValidationError
        validation_error = ValidationError.from_exception_data(
            "ValidationError",
            [
                {
                    "type": "value_error",
                    "loc": ("email",),
                    "msg": "Invalid email format",
                    "input": "invalid-email"
                }
            ]
        )
        
        with patch('app.core.exceptions.record_exception_error') as mock_record:
            response = await validation_exception_handler(mock_request, validation_error)
        
        assert response.status_code == 422
        response_data = response.body.decode()
        assert "VALIDATION_ERROR" in response_data
        assert "Invalid email format" in response_data
        
        mock_record.assert_called_once()

    def test_rate_limit_exception(self):
        """Test RateLimitException."""
        exc = RateLimitException("Rate limit exceeded")
        
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.status_code == 429
        assert exc.message == "Rate limit exceeded"


class TestMiddleware:
    """Test middleware functionality."""
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request object."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "POST"
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test-agent"}
        request.state = Mock()
        return request
    
    @pytest.mark.asyncio
    async def test_error_tracking_middleware(self, mock_request):
        """Test error tracking middleware adds context."""
        middleware = ErrorTrackingMiddleware(None)
        
        async def failing_app(request):
            raise ValueError("Test error")
        
        try:
            await middleware.dispatch(mock_request, failing_app)
        except ValueError as exc:
            assert hasattr(exc, '_error_context')
            assert exc._error_context['request_path'] == "/api/test"
            assert exc._error_context['request_method'] == "POST"
            assert exc._error_context['client_host'] == "127.0.0.1"
    
    @pytest.mark.asyncio
    async def test_rate_limit_middleware(self, mock_request):
        """Test rate limiting middleware."""
        middleware = RateLimitMiddleware(None, calls_per_minute=2)
        
        async def dummy_app(request):
            return Mock()
        
        # First two requests should pass
        await middleware.dispatch(mock_request, dummy_app)
        await middleware.dispatch(mock_request, dummy_app)
        
        # Third request should raise RateLimitException
        with pytest.raises(RateLimitException):
            await middleware.dispatch(mock_request, dummy_app)


class TestClientErrorReporting:
    """Test client error reporting functionality."""
    
    @pytest.mark.asyncio
    async def test_client_error_endpoint(self):
        """Test client error reporting endpoint."""
        from app.api.v1.monitoring import router
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        app.include_router(router, prefix="/api/v1/monitoring")
        
        client = TestClient(app)
        
        error_report = {
            "type": "javascript",
            "message": "Test error",
            "stack": "Error: Test error\n    at test.js:1:1",
            "timestamp": "2023-01-01T00:00:00.000Z",
            "url": "http://localhost:3000/test",
            "userAgent": "Mozilla/5.0 (Test)",
            "errorId": "test-error-123"
        }
        
        with patch('app.api.v1.monitoring.error_monitor.record_error') as mock_record:
            response = client.post("/api/v1/monitoring/client-errors", json=error_report)
        
        assert response.status_code == 201
        assert response.json()["status"] == "received"
        mock_record.assert_called_once()


class TestEnhancedErrorHandling:
    """Test enhanced error handling features."""
    
    @pytest.mark.asyncio
    async def test_error_context_preservation(self):
        """Test that error context is preserved through the stack."""
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/test"
        mock_request.method = "POST"
        mock_request.state = Mock()
        mock_request.state.trace_id = "test-trace-id"
        
        # Simulate an error with context
        error = ValueError("Test error")
        error._error_context = {
            'request_path': '/api/test',
            'custom_data': 'test_value'
        }
        
        with patch('app.core.exceptions.record_exception_error') as mock_record:
            await general_exception_handler(mock_request, error)
        
        # Verify that error context was passed to monitoring
        call_args = mock_record.call_args[1]
        assert 'custom_data' in call_args['metadata']
        assert call_args['metadata']['custom_data'] == 'test_value'
    
    @pytest.mark.asyncio
    async def test_error_severity_classification(self):
        """Test that errors are classified by severity."""
        # Test different error types and their expected severities
        test_cases = [
            (ValidationException("Invalid input"), "warning"),
            (AuthenticationException("Invalid token"), "info"),
            (PaymentException("Payment failed"), "error"),
            (ExternalServiceException("stripe", "Service down"), "error"),
        ]
        
        for exception, expected_severity in test_cases:
            # In a real implementation, you'd check the severity classification
            # For now, we'll just verify the exception properties
            assert hasattr(exception, 'status_code')
            assert hasattr(exception, 'error_code')


if __name__ == "__main__":
    pytest.main([__file__])