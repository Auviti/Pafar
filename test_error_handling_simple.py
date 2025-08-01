#!/usr/bin/env python3
"""
Simple test to verify error handling functionality is working.
"""
import sys
import os
import asyncio
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_error_monitoring():
    """Test basic error monitoring functionality."""
    try:
        from app.core.monitoring import ErrorMonitor, ErrorEvent
        
        print("✓ Successfully imported error monitoring components")
        
        # Create error monitor instance
        monitor = ErrorMonitor(max_events=10)
        
        # Record a test error
        await monitor.record_error(
            error_type="TEST_ERROR",
            error_message="This is a test error",
            trace_id="test-trace-123",
            service="test-service",
            severity="error"
        )
        
        print("✓ Successfully recorded error event")
        
        # Get recent errors
        recent_errors = monitor.get_recent_errors(limit=1)
        assert len(recent_errors) == 1
        assert recent_errors[0]["type"] == "TEST_ERROR"
        
        print("✓ Successfully retrieved error events")
        
        # Get error summary
        summary = monitor.get_error_summary(hours=1)
        assert summary["total_errors"] == 1
        assert "TEST_ERROR" in summary["error_types"]
        
        print("✓ Successfully generated error summary")
        
        return True
        
    except Exception as e:
        print(f"✗ Error monitoring test failed: {e}")
        return False

def test_custom_exceptions():
    """Test custom exception classes."""
    try:
        from app.core.exceptions import (
            PafarException,
            ValidationException,
            AuthenticationException,
            PaymentException
        )
        
        print("✓ Successfully imported custom exceptions")
        
        # Test PafarException
        exc = PafarException(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=400
        )
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.status_code == 400
        
        print("✓ PafarException working correctly")
        
        # Test ValidationException
        val_exc = ValidationException("Invalid input", "email")
        assert val_exc.error_code == "VALIDATION_ERROR"
        assert val_exc.status_code == 422
        
        print("✓ ValidationException working correctly")
        
        # Test AuthenticationException
        auth_exc = AuthenticationException("Invalid credentials")
        assert auth_exc.error_code == "AUTHENTICATION_ERROR"
        assert auth_exc.status_code == 401
        
        print("✓ AuthenticationException working correctly")
        
        # Test PaymentException
        pay_exc = PaymentException("Payment failed", "CARD_DECLINED")
        assert pay_exc.error_code == "PAYMENT_ERROR"
        assert pay_exc.status_code == 402
        
        print("✓ PaymentException working correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Custom exceptions test failed: {e}")
        return False

def test_fallback_mechanisms():
    """Test fallback mechanisms."""
    try:
        from app.core.fallbacks import CircuitBreaker, FallbackService
        
        print("✓ Successfully imported fallback mechanisms")
        
        # Test CircuitBreaker
        circuit_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)
        assert circuit_breaker.state == "CLOSED"
        
        print("✓ CircuitBreaker initialized correctly")
        
        # Test FallbackService
        fallback_service = FallbackService()
        fallback_service.register_fallback_data("test-service", {"fallback": "data"})
        
        retrieved_data = fallback_service.get_fallback_data("test-service")
        assert retrieved_data == {"fallback": "data"}
        
        print("✓ FallbackService working correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Fallback mechanisms test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Testing Error Handling Implementation")
    print("=" * 50)
    
    tests = [
        ("Custom Exceptions", test_custom_exceptions),
        ("Fallback Mechanisms", test_fallback_mechanisms),
        ("Error Monitoring", test_error_monitoring),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                print(f"✅ {test_name} test PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} test FAILED")
                
        except Exception as e:
            print(f"❌ {test_name} test FAILED with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All error handling tests passed!")
        return 0
    else:
        print("⚠️  Some error handling tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)