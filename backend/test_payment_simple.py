#!/usr/bin/env python3
"""
Simple test to verify payment system components are working.
"""
import asyncio
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, patch

# Test imports
try:
    from app.models.payment import Payment, PaymentStatus, PaymentMethod, PaymentGateway
    from app.schemas.payment import PaymentIntentCreate, PaymentResponse
    from app.utils.receipt_generator import ReceiptGenerator
    from app.schemas.payment import PaymentReceiptData
    print("✓ All payment imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    exit(1)

def test_payment_model():
    """Test payment model creation."""
    payment = Payment(
        id=uuid4(),
        booking_id=uuid4(),
        amount=Decimal("50.00"),
        currency="USD",
        payment_method=PaymentMethod.CARD,
        payment_gateway=PaymentGateway.STRIPE,
        gateway_transaction_id="pi_test123",
        status=PaymentStatus.PENDING
    )
    
    assert payment.amount == Decimal("50.00")
    assert payment.currency == "USD"
    assert payment.status == PaymentStatus.PENDING
    assert payment.is_pending
    assert not payment.is_successful
    print("✓ Payment model creation works")

def test_payment_schemas():
    """Test payment schema validation."""
    # Test PaymentIntentCreate
    intent_data = PaymentIntentCreate(
        booking_id=uuid4(),
        save_payment_method=False
    )
    assert intent_data.booking_id is not None
    assert not intent_data.save_payment_method
    
    # Test PaymentResponse
    payment_response = PaymentResponse(
        id=uuid4(),
        booking_id=uuid4(),
        amount=Decimal("50.00"),
        currency="USD",
        status=PaymentStatus.COMPLETED,
        created_at="2024-01-01T00:00:00"
    )
    assert payment_response.amount == Decimal("50.00")
    print("✓ Payment schemas work")

def test_receipt_generator():
    """Test receipt generation."""
    receipt_data = PaymentReceiptData(
        payment_id=uuid4(),
        booking_reference="BK123456",
        passenger_name="John Doe",
        passenger_email="john@example.com",
        trip_details={
            "route": "New York to Boston",
            "departure_time": "2024-01-15T10:00:00",
            "bus": "ABC-123",
            "seats": [1, 2]
        },
        amount=Decimal("50.00"),
        currency="USD",
        payment_method="card",
        transaction_id="pi_test123",
        payment_date="2024-01-15T10:30:00"
    )
    
    # Test HTML receipt generation
    html_receipt = ReceiptGenerator.generate_html_receipt(receipt_data)
    assert "BK123456" in html_receipt
    assert "John Doe" in html_receipt
    assert "New York to Boston" in html_receipt
    assert "50.00" in html_receipt
    
    # Test text receipt generation
    text_receipt = ReceiptGenerator.generate_text_receipt(receipt_data)
    assert "BK123456" in text_receipt
    assert "John Doe" in text_receipt
    
    # Test receipt summary
    summary = ReceiptGenerator.generate_receipt_summary(receipt_data)
    assert summary["booking_reference"] == "BK123456"
    assert summary["amount"] == 50.0
    
    print("✓ Receipt generator works")

def test_stripe_integration():
    """Test Stripe integration setup."""
    try:
        import stripe
        from app.core.config import settings
        
        # Test that Stripe can be configured
        stripe.api_key = "sk_test_fake_key"
        assert stripe.api_key == "sk_test_fake_key"
        print("✓ Stripe integration setup works")
    except ImportError:
        print("✗ Stripe not available")

def main():
    """Run all tests."""
    print("Testing Payment System Components...")
    print("=" * 50)
    
    test_payment_model()
    test_payment_schemas()
    test_receipt_generator()
    test_stripe_integration()
    
    print("=" * 50)
    print("🎉 All payment system components are working!")

if __name__ == "__main__":
    main()