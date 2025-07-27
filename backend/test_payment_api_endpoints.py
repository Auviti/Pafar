"""
Integration tests for payment API endpoints.
"""
import asyncio
import pytest
from decimal import Decimal
from uuid import uuid4
from unittest.mock import patch, Mock
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus, PaymentMethod, PaymentGateway


# Mock database session
class MockDB:
    def __init__(self):
        self.committed = False
        self.added_objects = []
    
    async def execute(self, query):
        # Mock result that returns our test data
        result = Mock()
        result.scalar_one_or_none.return_value = None
        return result
    
    def add(self, obj):
        self.added_objects.append(obj)
    
    async def commit(self):
        self.committed = True
    
    async def refresh(self, obj):
        pass


# Mock current user
def mock_current_user():
    return User(
        id=uuid4(),
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        role=UserRole.PASSENGER,
        is_verified=True,
        is_active=True
    )


# Override dependencies
app.dependency_overrides[get_db] = lambda: MockDB()
app.dependency_overrides[get_current_user] = mock_current_user


async def test_payment_endpoints():
    """Test payment API endpoints integration."""
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        
        # Test payment intent creation
        with patch('stripe.PaymentIntent.create') as mock_stripe_create:
            mock_payment_intent = Mock()
            mock_payment_intent.id = "pi_test123"
            mock_payment_intent.client_secret = "pi_test123_secret"
            mock_payment_intent.status = "requires_payment_method"
            mock_payment_intent.next_action = None
            mock_stripe_create.return_value = mock_payment_intent
            
            # Mock booking lookup
            with patch('app.services.payment_service.PaymentService._get_booking_with_details') as mock_get_booking:
                mock_booking = Mock()
                mock_booking.id = uuid4()
                mock_booking.user_id = mock_current_user().id
                mock_booking.total_amount = Decimal("50.00")
                mock_booking.payment_status = "pending"
                mock_get_booking.return_value = mock_booking
                
                response = await client.post(
                    "/api/v1/payments/payment-intent",
                    json={
                        "booking_id": str(mock_booking.id),
                        "save_payment_method": False
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["payment_intent_id"] == "pi_test123"
                assert data["client_secret"] == "pi_test123_secret"
                assert data["amount"] == 50.0
                assert data["currency"] == "USD"
                
                print("✓ Payment intent creation endpoint works")
        
        # Test payment method creation
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
            
            response = await client.post(
                "/api/v1/payments/payment-methods",
                json={
                    "card_number": "4242424242424242",
                    "exp_month": 12,
                    "exp_year": 2025,
                    "cvc": "123",
                    "cardholder_name": "John Doe"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["token_id"] == "pm_test123"
            assert data["last_four"] == "4242"
            assert data["brand"] == "visa"
            
            print("✓ Payment method creation endpoint works")
        
        # Test webhook endpoint
        webhook_payload = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test123",
                    "status": "succeeded"
                }
            }
        }
        
        with patch('app.services.payment_service.PaymentService.handle_webhook_event') as mock_webhook:
            mock_webhook.return_value = True
            
            response = await client.post(
                "/api/v1/payments/webhook",
                json=webhook_payload
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            
            print("✓ Webhook endpoint works")
        
        print("\n🎉 Payment API endpoints integration test passed!")


if __name__ == "__main__":
    asyncio.run(test_payment_endpoints())