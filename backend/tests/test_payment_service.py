"""
Unit tests for payment service.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from decimal import Decimal
from datetime import datetime
from uuid import uuid4
import stripe

from app.services.payment_service import (
    PaymentService, PaymentServiceError, PaymentNotFoundError, 
    PaymentProcessingError
)
from app.models.payment import Payment, PaymentStatus, PaymentMethod, PaymentGateway
from app.models.booking import Booking, BookingStatus
from app.models.user import User, UserRole
from app.models.fleet import Trip, Route, Terminal, Bus
from app.schemas.payment import (
    PaymentIntentCreate, PaymentConfirmation, PaymentMethodTokenCreate,
    PaymentRetryRequest
)


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def payment_service(mock_db):
    """Payment service instance with mocked database."""
    return PaymentService(mock_db)


@pytest.fixture
def sample_user():
    """Sample user for testing."""
    return User(
        id=uuid4(),
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        role=UserRole.PASSENGER,
        is_verified=True,
        is_active=True
    )


@pytest.fixture
def sample_terminal():
    """Sample terminal for testing."""
    return Terminal(
        id=uuid4(),
        name="Central Station",
        city="Test City",
        address="123 Main St"
    )


@pytest.fixture
def sample_route(sample_terminal):
    """Sample route for testing."""
    destination = Terminal(
        id=uuid4(),
        name="North Station",
        city="Test City",
        address="456 North St"
    )
    return Route(
        id=uuid4(),
        origin_terminal=sample_terminal,
        destination_terminal=destination,
        distance_km=Decimal("50.0"),
        estimated_duration_minutes=60,
        base_fare=Decimal("25.00")
    )


@pytest.fixture
def sample_bus():
    """Sample bus for testing."""
    return Bus(
        id=uuid4(),
        license_plate="ABC-123",
        model="Mercedes Sprinter",
        capacity=20
    )


@pytest.fixture
def sample_trip(sample_route, sample_bus, sample_user):
    """Sample trip for testing."""
    return Trip(
        id=uuid4(),
        route=sample_route,
        bus=sample_bus,
        driver_id=sample_user.id,
        departure_time=datetime(2024, 1, 15, 10, 0),
        fare=Decimal("25.00"),
        available_seats=18
    )


@pytest.fixture
def sample_booking(sample_user, sample_trip):
    """Sample booking for testing."""
    return Booking(
        id=uuid4(),
        user_id=sample_user.id,
        user=sample_user,
        trip_id=sample_trip.id,
        trip=sample_trip,
        seat_numbers=[1, 2],
        total_amount=Decimal("50.00"),
        status=BookingStatus.CONFIRMED,
        booking_reference="BK123456",
        payment_status="pending"
    )


@pytest.fixture
def sample_payment(sample_booking):
    """Sample payment for testing."""
    return Payment(
        id=uuid4(),
        booking_id=sample_booking.id,
        booking=sample_booking,
        amount=Decimal("50.00"),
        currency="USD",
        payment_method=PaymentMethod.CARD,
        payment_gateway=PaymentGateway.STRIPE,
        gateway_transaction_id="pi_test123",
        status=PaymentStatus.PENDING
    )


class TestPaymentService:
    """Test cases for PaymentService."""
    
    @pytest.mark.asyncio
    @patch('stripe.PaymentIntent.create')
    async def test_create_payment_intent_success(
        self, mock_stripe_create, payment_service, mock_db, sample_user, sample_booking
    ):
        """Test successful payment intent creation."""
        # Mock Stripe response
        mock_payment_intent = Mock()
        mock_payment_intent.id = "pi_test123"
        mock_payment_intent.client_secret = "pi_test123_secret"
        mock_payment_intent.status = "requires_payment_method"
        mock_payment_intent.next_action = None
        mock_stripe_create.return_value = mock_payment_intent
        
        # Mock database queries
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_booking
        mock_db.execute.return_value = mock_result
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Test data
        payment_data = PaymentIntentCreate(
            booking_id=sample_booking.id,
            save_payment_method=False
        )
        
        # Execute
        result = await payment_service.create_payment_intent(sample_user.id, payment_data)
        
        # Assertions
        assert result.payment_intent_id == "pi_test123"
        assert result.client_secret == "pi_test123_secret"
        assert result.amount == Decimal("50.00")
        assert result.currency == "USD"
        assert result.status == "requires_payment_method"
        assert not result.requires_action
        
        # Verify Stripe was called correctly
        mock_stripe_create.assert_called_once()
        call_args = mock_stripe_create.call_args[1]
        assert call_args["amount"] == 5000  # Amount in cents
        assert call_args["currency"] == "usd"
        assert str(sample_booking.id) in call_args["metadata"]["booking_id"]
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_payment_intent_booking_not_found(
        self, payment_service, mock_db, sample_user
    ):
        """Test payment intent creation with non-existent booking."""
        # Mock database to return None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        payment_data = PaymentIntentCreate(booking_id=uuid4())
        
        # Execute and assert
        with pytest.raises(PaymentServiceError, match="Booking not found"):
            await payment_service.create_payment_intent(sample_user.id, payment_data)
    
    @pytest.mark.asyncio
    async def test_create_payment_intent_unauthorized_user(
        self, payment_service, mock_db, sample_booking
    ):
        """Test payment intent creation with unauthorized user."""
        # Mock database to return booking with different user
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_booking
        mock_db.execute.return_value = mock_result
        
        unauthorized_user_id = uuid4()
        payment_data = PaymentIntentCreate(booking_id=sample_booking.id)
        
        # Execute and assert
        with pytest.raises(PaymentServiceError, match="Unauthorized access"):
            await payment_service.create_payment_intent(unauthorized_user_id, payment_data)
    
    @pytest.mark.asyncio
    async def test_create_payment_intent_already_paid(
        self, payment_service, mock_db, sample_user, sample_booking
    ):
        """Test payment intent creation for already paid booking."""
        # Set booking as already paid
        sample_booking.payment_status = "completed"
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_booking
        mock_db.execute.return_value = mock_result
        
        payment_data = PaymentIntentCreate(booking_id=sample_booking.id)
        
        # Execute and assert
        with pytest.raises(PaymentServiceError, match="already paid"):
            await payment_service.create_payment_intent(sample_user.id, payment_data)
    
    @pytest.mark.asyncio
    @patch('stripe.PaymentIntent.create')
    async def test_create_payment_intent_stripe_error(
        self, mock_stripe_create, payment_service, mock_db, sample_user, sample_booking
    ):
        """Test payment intent creation with Stripe error."""
        # Mock Stripe error
        mock_stripe_create.side_effect = stripe.error.CardError(
            "Your card was declined.", None, "card_declined"
        )
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_booking
        mock_db.execute.return_value = mock_result
        
        payment_data = PaymentIntentCreate(booking_id=sample_booking.id)
        
        # Execute and assert
        with pytest.raises(PaymentProcessingError):
            await payment_service.create_payment_intent(sample_user.id, payment_data)
    
    @pytest.mark.asyncio
    @patch('stripe.PaymentIntent.retrieve')
    async def test_confirm_payment_success(
        self, mock_stripe_retrieve, payment_service, mock_db, sample_user, 
        sample_booking, sample_payment
    ):
        """Test successful payment confirmation."""
        # Mock Stripe response
        mock_payment_intent = Mock()
        mock_payment_intent.status = "succeeded"
        mock_stripe_retrieve.return_value = mock_payment_intent
        
        # Mock database queries
        mock_result1 = AsyncMock()
        mock_result1.scalar_one_or_none.return_value = sample_payment
        mock_result2 = AsyncMock()
        mock_result2.scalar_one_or_none.return_value = sample_booking
        mock_db.execute.side_effect = [mock_result1, mock_result2]
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        confirmation_data = PaymentConfirmation(payment_intent_id="pi_test123")
        
        # Execute
        result = await payment_service.confirm_payment(sample_user.id, confirmation_data)
        
        # Assertions
        assert result.status == PaymentStatus.COMPLETED
        assert sample_payment.status == PaymentStatus.COMPLETED
        assert sample_payment.processed_at is not None
        
        mock_stripe_retrieve.assert_called_once_with("pi_test123")
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('stripe.PaymentIntent.retrieve')
    async def test_confirm_payment_requires_action(
        self, mock_stripe_retrieve, payment_service, mock_db, sample_user,
        sample_booking, sample_payment
    ):
        """Test payment confirmation requiring additional action."""
        # Mock Stripe response
        mock_payment_intent = Mock()
        mock_payment_intent.status = "requires_action"
        mock_stripe_retrieve.return_value = mock_payment_intent
        
        # Mock database queries
        mock_result1 = AsyncMock()
        mock_result1.scalar_one_or_none.return_value = sample_payment
        mock_result2 = AsyncMock()
        mock_result2.scalar_one_or_none.return_value = sample_booking
        mock_db.execute.side_effect = [mock_result1, mock_result2]
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        confirmation_data = PaymentConfirmation(payment_intent_id="pi_test123")
        
        # Execute
        result = await payment_service.confirm_payment(sample_user.id, confirmation_data)
        
        # Assertions
        assert result.status == PaymentStatus.PROCESSING
        assert sample_payment.status == PaymentStatus.PROCESSING
    
    @pytest.mark.asyncio
    async def test_confirm_payment_not_found(
        self, payment_service, mock_db, sample_user
    ):
        """Test payment confirmation with non-existent payment."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        confirmation_data = PaymentConfirmation(payment_intent_id="pi_nonexistent")
        
        # Execute and assert
        with pytest.raises(PaymentNotFoundError):
            await payment_service.confirm_payment(sample_user.id, confirmation_data)
    
    @pytest.mark.asyncio
    @patch('stripe.PaymentMethod.create')
    @patch('stripe.Customer.list')
    @patch('stripe.Customer.create')
    async def test_create_payment_method_token_success(
        self, mock_customer_create, mock_customer_list, mock_payment_method_create,
        payment_service, mock_db, sample_user
    ):
        """Test successful payment method token creation."""
        # Mock Stripe responses
        mock_payment_method = Mock()
        mock_payment_method.id = "pm_test123"
        mock_payment_method.card.last4 = "4242"
        mock_payment_method.card.brand = "visa"
        mock_payment_method.card.exp_month = 12
        mock_payment_method.card.exp_year = 2025
        mock_payment_method.attach = Mock()
        mock_payment_method_create.return_value = mock_payment_method
        
        mock_customer_list.return_value.data = []
        mock_customer = Mock()
        mock_customer.id = "cus_test123"
        mock_customer_create.return_value = mock_customer
        
        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = mock_result
        
        card_data = PaymentMethodTokenCreate(
            card_number="4242424242424242",
            exp_month=12,
            exp_year=2025,
            cvc="123",
            cardholder_name="John Doe"
        )
        
        # Execute
        result = await payment_service.create_payment_method_token(sample_user.id, card_data)
        
        # Assertions
        assert result.token_id == "pm_test123"
        assert result.last_four == "4242"
        assert result.brand == "visa"
        assert result.exp_month == 12
        assert result.exp_year == 2025
        
        # Verify Stripe calls
        mock_payment_method_create.assert_called_once()
        mock_payment_method.attach.assert_called_once_with(customer="cus_test123")
    
    @pytest.mark.asyncio
    @patch('stripe.Customer.list')
    @patch('stripe.PaymentMethod.list')
    async def test_get_saved_payment_methods_success(
        self, mock_payment_method_list, mock_customer_list,
        payment_service, mock_db, sample_user
    ):
        """Test successful retrieval of saved payment methods."""
        # Mock Stripe responses
        mock_customer_list.return_value.data = [Mock(id="cus_test123")]
        
        mock_pm1 = Mock()
        mock_pm1.id = "pm_test1"
        mock_pm1.card.last4 = "4242"
        mock_pm1.card.brand = "visa"
        mock_pm1.card.exp_month = 12
        mock_pm1.card.exp_year = 2025
        mock_pm1.created = 1640995200  # Unix timestamp
        
        mock_payment_method_list.return_value.data = [mock_pm1]
        
        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = mock_result
        
        # Execute
        result = await payment_service.get_saved_payment_methods(sample_user.id)
        
        # Assertions
        assert result.total == 1
        assert len(result.payment_methods) == 1
        assert result.payment_methods[0].id == "pm_test1"
        assert result.payment_methods[0].last_four == "4242"
        assert result.payment_methods[0].brand == "visa"
    
    @pytest.mark.asyncio
    async def test_get_saved_payment_methods_no_customer(
        self, payment_service, mock_db, sample_user
    ):
        """Test retrieval of payment methods when user has no Stripe customer."""
        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = mock_result
        
        with patch('stripe.Customer.list') as mock_customer_list:
            mock_customer_list.return_value.data = []
            
            # Execute
            result = await payment_service.get_saved_payment_methods(sample_user.id)
            
            # Assertions
            assert result.total == 0
            assert len(result.payment_methods) == 0
    
    @pytest.mark.asyncio
    async def test_retry_payment_success(
        self, payment_service, mock_db, sample_user, sample_booking, sample_payment
    ):
        """Test successful payment retry."""
        # Mock database queries
        mock_result1 = AsyncMock()
        mock_result1.scalar_one_or_none.return_value = sample_payment
        mock_result2 = AsyncMock()
        mock_result2.scalar_one_or_none.return_value = sample_booking
        mock_db.execute.side_effect = [mock_result1, mock_result2]
        
        # Mock the create_payment_intent method
        with patch.object(payment_service, 'create_payment_intent') as mock_create:
            mock_create.return_value = Mock(payment_intent_id="pi_retry123")
            
            retry_data = PaymentRetryRequest(
                payment_id=sample_payment.id,
                payment_method_token="pm_test123"
            )
            
            # Execute
            result = await payment_service.retry_payment(sample_user.id, retry_data)
            
            # Assertions
            assert result.payment_intent_id == "pi_retry123"
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retry_payment_already_completed(
        self, payment_service, mock_db, sample_user, sample_booking, sample_payment
    ):
        """Test retry of already completed payment."""
        # Set payment as completed
        sample_payment.status = PaymentStatus.COMPLETED
        
        mock_result1 = AsyncMock()
        mock_result1.scalar_one_or_none.return_value = sample_payment
        mock_result2 = AsyncMock()
        mock_result2.scalar_one_or_none.return_value = sample_booking
        mock_db.execute.side_effect = [mock_result1, mock_result2]
        
        retry_data = PaymentRetryRequest(payment_id=sample_payment.id)
        
        # Execute and assert
        with pytest.raises(PaymentServiceError, match="already completed"):
            await payment_service.retry_payment(sample_user.id, retry_data)
    
    @pytest.mark.asyncio
    async def test_handle_webhook_event_success(
        self, payment_service, mock_db, sample_payment
    ):
        """Test successful webhook event handling."""
        # Mock database queries
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_payment
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        
        event_data = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test123",
                    "status": "succeeded"
                }
            }
        }
        
        # Execute
        result = await payment_service.handle_webhook_event(event_data)
        
        # Assertions
        assert result is True
        assert sample_payment.status == PaymentStatus.COMPLETED
        assert sample_payment.processed_at is not None
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_webhook_event_payment_failed(
        self, payment_service, mock_db, sample_payment
    ):
        """Test webhook event handling for failed payment."""
        mock_db.execute.return_value.scalar_one_or_none.return_value = sample_payment
        mock_db.commit = AsyncMock()
        
        event_data = {
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": "pi_test123",
                    "status": "payment_failed"
                }
            }
        }
        
        # Execute
        result = await payment_service.handle_webhook_event(event_data)
        
        # Assertions
        assert result is True
        assert sample_payment.status == PaymentStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_handle_webhook_event_payment_not_found(
        self, payment_service, mock_db
    ):
        """Test webhook event handling when payment is not found."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        event_data = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_nonexistent"
                }
            }
        }
        
        # Execute
        result = await payment_service.handle_webhook_event(event_data)
        
        # Assertions
        assert result is False
    
    @pytest.mark.asyncio
    async def test_generate_receipt_data_success(
        self, payment_service, mock_db, sample_payment, sample_booking, 
        sample_user, sample_trip
    ):
        """Test successful receipt data generation."""
        # Set payment as completed
        sample_payment.status = PaymentStatus.COMPLETED
        sample_payment.processed_at = datetime.utcnow()
        
        # Mock database query with relationships
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_payment
        mock_db.execute.return_value = mock_result
        
        # Execute
        result = await payment_service.generate_receipt_data(sample_payment.id)
        
        # Assertions
        assert result.payment_id == sample_payment.id
        assert result.booking_reference == sample_booking.booking_reference
        assert result.passenger_name == f"{sample_user.first_name} {sample_user.last_name}"
        assert result.passenger_email == sample_user.email
        assert result.amount == sample_payment.amount
        assert result.currency == sample_payment.currency
        assert "seats" in result.trip_details
    
    @pytest.mark.asyncio
    async def test_generate_receipt_data_payment_not_completed(
        self, payment_service, mock_db, sample_payment
    ):
        """Test receipt generation for non-completed payment."""
        # Keep payment as pending
        sample_payment.status = PaymentStatus.PENDING
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_payment
        mock_db.execute.return_value = mock_result
        
        # Execute and assert
        with pytest.raises(PaymentServiceError, match="not completed"):
            await payment_service.generate_receipt_data(sample_payment.id)