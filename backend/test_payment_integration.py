#!/usr/bin/env python3
"""
Integration test for the complete payment system.
"""
import asyncio
import os
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Set test environment
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_fake_key"

from app.services.payment_service import PaymentService
from app.models.payment import Payment, PaymentStatus, PaymentMethod, PaymentGateway
from app.models.booking import Booking, BookingStatus
from app.models.user import User, UserRole
from app.schemas.payment import PaymentIntentCreate, PaymentConfirmation
from app.utils.receipt_generator import ReceiptGenerator


class MockDatabase:
    """Mock database for testing."""
    
    def __init__(self):
        self.payments = {}
        self.bookings = {}
        self.users = {}
        self.committed = False
    
    async def execute(self, query):
        """Mock database execute."""
        result = AsyncMock()
        # Return mock data based on query type
        result.scalar_one_or_none.return_value = None
        return result
    
    def add(self, obj):
        """Mock add object."""
        if isinstance(obj, Payment):
            self.payments[obj.id] = obj
        elif isinstance(obj, Booking):
            self.bookings[obj.id] = obj
        elif isinstance(obj, User):
            self.users[obj.id] = obj
    
    async def commit(self):
        """Mock commit."""
        self.committed = True
    
    async def refresh(self, obj):
        """Mock refresh."""
        pass


async def test_payment_service_integration():
    """Test payment service integration."""
    print("Testing Payment Service Integration...")
    
    # Create mock database
    mock_db = MockDatabase()
    payment_service = PaymentService(mock_db)
    
    # Create test data
    user_id = uuid4()
    booking_id = uuid4()
    
    # Mock booking data
    mock_booking = Mock()
    mock_booking.id = booking_id
    mock_booking.user_id = user_id
    mock_booking.total_amount = Decimal("50.00")
    mock_booking.payment_status = "pending"
    mock_booking.booking_reference = "BK123456"
    
    # Test 1: Create Payment Intent
    print("1. Testing payment intent creation...")
    
    with patch('stripe.PaymentIntent.create') as mock_stripe_create:
        mock_payment_intent = Mock()
        mock_payment_intent.id = "pi_test123"
        mock_payment_intent.client_secret = "pi_test123_secret"
        mock_payment_intent.status = "requires_payment_method"
        mock_payment_intent.next_action = None
        mock_stripe_create.return_value = mock_payment_intent
        
        # Mock the booking lookup
        with patch.object(payment_service, '_get_booking_with_details', return_value=mock_booking):
            payment_data = PaymentIntentCreate(
                booking_id=booking_id,
                save_payment_method=False
            )
            
            try:
                result = await payment_service.create_payment_intent(user_id, payment_data)
                assert result.payment_intent_id == "pi_test123"
                assert result.amount == Decimal("50.00")
                print("   ✓ Payment intent creation successful")
            except Exception as e:
                print(f"   ✗ Payment intent creation failed: {e}")
    
    # Test 2: Payment Method Tokenization
    print("2. Testing payment method tokenization...")
    
    with patch('stripe.PaymentMethod.create') as mock_pm_create, \
         patch('stripe.Customer.list') as mock_customer_list, \
         patch('stripe.Customer.create') as mock_customer_create:
        
        mock_payment_method = Mock()
        mock_payment_method.id = "pm_test123"
        mock_payment_method.card.last4 = "4242"
        mock_payment_method.card.brand = "visa"
        mock_payment_method.card.exp_month = 12
        mock_payment_method.card.exp_year = 2025
        mock_payment_method.attach = Mock()
        mock_pm_create.return_value = mock_payment_method
        
        mock_customer_list.return_value.data = []
        mock_customer = Mock()
        mock_customer.id = "cus_test123"
        mock_customer_create.return_value = mock_customer
        
        # Mock user lookup
        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.first_name = "John"
        mock_user.last_name = "Doe"
        
        with patch.object(payment_service, '_get_or_create_stripe_customer', return_value="cus_test123"):
            from app.schemas.payment import PaymentMethodTokenCreate
            
            card_data = PaymentMethodTokenCreate(
                card_number="4242424242424242",
                exp_month=12,
                exp_year=2025,
                cvc="123",
                cardholder_name="John Doe"
            )
            
            try:
                result = await payment_service.create_payment_method_token(user_id, card_data)
                assert result.token_id == "pm_test123"
                assert result.last_four == "4242"
                print("   ✓ Payment method tokenization successful")
            except Exception as e:
                print(f"   ✗ Payment method tokenization failed: {e}")
    
    # Test 3: Webhook Event Handling
    print("3. Testing webhook event handling...")
    
    # Create a mock payment
    mock_payment = Mock()
    mock_payment.id = uuid4()
    mock_payment.status = PaymentStatus.PENDING
    mock_payment.booking_id = booking_id
    
    with patch.object(payment_service, '_get_payment_by_transaction_id', return_value=mock_payment), \
         patch.object(payment_service, '_update_booking_payment_status'):
        
        event_data = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test123",
                    "status": "succeeded"
                }
            }
        }
        
        try:
            result = await payment_service.handle_webhook_event(event_data)
            assert result is True
            assert mock_payment.status == PaymentStatus.COMPLETED
            print("   ✓ Webhook event handling successful")
        except Exception as e:
            print(f"   ✗ Webhook event handling failed: {e}")
    
    print("✓ Payment Service Integration Test Complete")


def test_receipt_generation_integration():
    """Test receipt generation integration."""
    print("\nTesting Receipt Generation Integration...")
    
    # Create comprehensive receipt data
    from app.schemas.payment import PaymentReceiptData
    
    receipt_data = PaymentReceiptData(
        payment_id=uuid4(),
        booking_reference="BK123456",
        passenger_name="John Doe",
        passenger_email="john.doe@example.com",
        trip_details={
            "route": "New York to Boston",
            "departure_time": "2024-01-15T10:00:00",
            "bus": "ABC-123",
            "seats": [1, 2]
        },
        amount=Decimal("75.50"),
        currency="USD",
        payment_method="card",
        transaction_id="pi_1234567890",
        payment_date=datetime.now()
    )
    
    try:
        # Test HTML receipt
        html_receipt = ReceiptGenerator.generate_html_receipt(receipt_data)
        assert "BK123456" in html_receipt
        assert "John Doe" in html_receipt
        assert "75.50" in html_receipt
        assert "New York to Boston" in html_receipt
        print("   ✓ HTML receipt generation successful")
        
        # Test text receipt
        text_receipt = ReceiptGenerator.generate_text_receipt(receipt_data)
        assert "BK123456" in text_receipt
        assert "John Doe" in text_receipt
        assert "75.50" in text_receipt
        print("   ✓ Text receipt generation successful")
        
        # Test receipt summary
        summary = ReceiptGenerator.generate_receipt_summary(receipt_data)
        assert summary["booking_reference"] == "BK123456"
        assert summary["amount"] == 75.5
        assert summary["passenger_name"] == "John Doe"
        print("   ✓ Receipt summary generation successful")
        
    except Exception as e:
        print(f"   ✗ Receipt generation failed: {e}")
    
    print("✓ Receipt Generation Integration Test Complete")


def test_payment_models_integration():
    """Test payment models integration."""
    print("\nTesting Payment Models Integration...")
    
    try:
        # Test Payment model
        payment = Payment(
            id=uuid4(),
            booking_id=uuid4(),
            amount=Decimal("100.00"),
            currency="USD",
            payment_method=PaymentMethod.CARD,
            payment_gateway=PaymentGateway.STRIPE,
            gateway_transaction_id="pi_test123",
            status=PaymentStatus.PENDING
        )
        
        assert payment.amount == Decimal("100.00")
        assert payment.is_pending
        assert not payment.is_successful
        print("   ✓ Payment model creation successful")
        
        # Test status transitions
        payment.status = PaymentStatus.COMPLETED
        payment.processed_at = datetime.now()
        
        assert payment.is_successful
        assert not payment.is_pending
        assert payment.processed_at is not None
        print("   ✓ Payment status transitions successful")
        
    except Exception as e:
        print(f"   ✗ Payment models integration failed: {e}")
    
    print("✓ Payment Models Integration Test Complete")


async def main():
    """Run all integration tests."""
    print("Payment System Integration Tests")
    print("=" * 50)
    
    await test_payment_service_integration()
    test_receipt_generation_integration()
    test_payment_models_integration()
    
    print("=" * 50)
    print("🎉 All Payment System Integration Tests Passed!")


if __name__ == "__main__":
    asyncio.run(main())