"""
Unit tests for service layer components.
"""
import pytest
import uuid
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.auth_service import AuthService
from app.services.booking_service import BookingService
from app.services.payment_service import PaymentService
from app.services.tracking_service import TrackingService
from app.services.fleet_service import FleetService
from app.models.user import User, UserRole
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.models.fleet import Trip, TripStatus
from backend.tests.factories import (
    UserFactory, BookingFactory, PaymentFactory, 
    TripFactory, TestDataBuilder
)


class TestAuthService:
    """Test authentication service functionality."""
    
    @pytest.fixture
    def auth_service(self):
        """Create auth service with mocked dependencies."""
        mock_db = AsyncMock()
        mock_redis = Mock()
        return AuthService(db=mock_db, redis=mock_redis)
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, auth_service):
        """Test successful user creation."""
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        # Mock database operations
        auth_service.db.execute = AsyncMock()
        auth_service.db.commit = AsyncMock()
        
        with patch('app.services.auth_service.hash_password') as mock_hash:
            mock_hash.return_value = "hashed_password"
            
            result = await auth_service.create_user(user_data)
            
            assert result is not None
            mock_hash.assert_called_once_with("password123")
            auth_service.db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service):
        """Test successful user authentication."""
        user = UserFactory.create(
            email="test@example.com",
            password_hash="hashed_password"
        )
        
        # Mock database query
        auth_service.db.execute = AsyncMock()
        auth_service.db.execute.return_value.scalar_one_or_none.return_value = user
        
        with patch('app.services.auth_service.verify_password') as mock_verify:
            mock_verify.return_value = True
            
            result = await auth_service.authenticate_user("test@example.com", "password123")
            
            assert result == user
            mock_verify.assert_called_once_with("password123", "hashed_password")
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_credentials(self, auth_service):
        """Test authentication with invalid credentials."""
        # Mock database query returning None
        auth_service.db.execute = AsyncMock()
        auth_service.db.execute.return_value.scalar_one_or_none.return_value = None
        
        result = await auth_service.authenticate_user("invalid@example.com", "wrong_password")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_tokens(self, auth_service):
        """Test JWT token generation."""
        user = UserFactory.create()
        
        with patch('app.services.auth_service.create_access_token') as mock_access, \
             patch('app.services.auth_service.create_refresh_token') as mock_refresh:
            
            mock_access.return_value = "access_token"
            mock_refresh.return_value = "refresh_token"
            
            tokens = await auth_service.generate_tokens(user)
            
            assert tokens["access_token"] == "access_token"
            assert tokens["refresh_token"] == "refresh_token"
            assert tokens["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_verify_email_success(self, auth_service):
        """Test email verification."""
        user = UserFactory.create(is_verified=False)
        verification_token = "valid_token"
        
        # Mock Redis operations
        auth_service.redis.get = AsyncMock(return_value=str(user.id))
        auth_service.redis.delete = AsyncMock()
        auth_service.db.execute = AsyncMock()
        auth_service.db.commit = AsyncMock()
        
        result = await auth_service.verify_email(verification_token)
        
        assert result is True
        auth_service.redis.delete.assert_called_once_with(f"email_verification:{verification_token}")
    
    @pytest.mark.asyncio
    async def test_reset_password_success(self, auth_service):
        """Test password reset functionality."""
        user = UserFactory.create()
        reset_token = "valid_reset_token"
        new_password = "new_password123"
        
        # Mock Redis and database operations
        auth_service.redis.get = AsyncMock(return_value=str(user.id))
        auth_service.redis.delete = AsyncMock()
        auth_service.db.execute = AsyncMock()
        auth_service.db.commit = AsyncMock()
        
        with patch('app.services.auth_service.hash_password') as mock_hash:
            mock_hash.return_value = "new_hashed_password"
            
            result = await auth_service.reset_password(reset_token, new_password)
            
            assert result is True
            mock_hash.assert_called_once_with(new_password)


class TestBookingService:
    """Test booking service functionality."""
    
    @pytest.fixture
    def booking_service(self):
        """Create booking service with mocked dependencies."""
        mock_db = AsyncMock()
        mock_redis = Mock()
        return BookingService(db=mock_db, redis=mock_redis)
    
    @pytest.mark.asyncio
    async def test_search_trips_success(self, booking_service):
        """Test trip search functionality."""
        search_params = {
            "origin_terminal_id": str(uuid.uuid4()),
            "destination_terminal_id": str(uuid.uuid4()),
            "departure_date": "2024-12-25"
        }
        
        mock_trips = [TripFactory.create() for _ in range(3)]
        
        # Mock database query
        booking_service.db.execute = AsyncMock()
        booking_service.db.execute.return_value.scalars.return_value.all.return_value = mock_trips
        
        result = await booking_service.search_trips(search_params)
        
        assert len(result) == 3
        assert all(isinstance(trip, type(mock_trips[0])) for trip in result)
    
    @pytest.mark.asyncio
    async def test_create_booking_success(self, booking_service):
        """Test successful booking creation."""
        booking_data = {
            "trip_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "seat_numbers": [1, 2],
            "total_amount": Decimal("60.00")
        }
        
        trip = TripFactory.create(available_seats=10)
        
        # Mock database operations
        booking_service.db.execute = AsyncMock()
        booking_service.db.execute.return_value.scalar_one_or_none.return_value = trip
        booking_service.db.add = Mock()
        booking_service.db.commit = AsyncMock()
        
        # Mock seat availability check
        with patch.object(booking_service, '_check_seat_availability', return_value=True):
            result = await booking_service.create_booking(booking_data)
            
            assert result is not None
            booking_service.db.add.assert_called_once()
            booking_service.db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_booking_seats_unavailable(self, booking_service):
        """Test booking creation with unavailable seats."""
        booking_data = {
            "trip_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "seat_numbers": [1, 2],
            "total_amount": Decimal("60.00")
        }
        
        trip = TripFactory.create(available_seats=0)
        
        # Mock database operations
        booking_service.db.execute = AsyncMock()
        booking_service.db.execute.return_value.scalar_one_or_none.return_value = trip
        
        # Mock seat availability check
        with patch.object(booking_service, '_check_seat_availability', return_value=False):
            with pytest.raises(Exception):  # Should raise BookingNotAvailableException
                await booking_service.create_booking(booking_data)
    
    @pytest.mark.asyncio
    async def test_cancel_booking_success(self, booking_service):
        """Test successful booking cancellation."""
        booking = BookingFactory.create(status=BookingStatus.CONFIRMED)
        
        # Mock database operations
        booking_service.db.execute = AsyncMock()
        booking_service.db.execute.return_value.scalar_one_or_none.return_value = booking
        booking_service.db.commit = AsyncMock()
        
        # Mock cancellation policy check
        with patch.object(booking_service, '_can_cancel_booking', return_value=True):
            result = await booking_service.cancel_booking(str(booking.id))
            
            assert result is True
            booking_service.db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_bookings(self, booking_service):
        """Test retrieving user bookings."""
        user_id = str(uuid.uuid4())
        mock_bookings = [BookingFactory.create() for _ in range(3)]
        
        # Mock database query
        booking_service.db.execute = AsyncMock()
        booking_service.db.execute.return_value.scalars.return_value.all.return_value = mock_bookings
        
        result = await booking_service.get_user_bookings(user_id)
        
        assert len(result) == 3
        assert all(isinstance(booking, type(mock_bookings[0])) for booking in result)


class TestPaymentService:
    """Test payment service functionality."""
    
    @pytest.fixture
    def payment_service(self):
        """Create payment service with mocked dependencies."""
        mock_db = AsyncMock()
        mock_stripe = Mock()
        return PaymentService(db=mock_db, stripe_client=mock_stripe)
    
    @pytest.mark.asyncio
    async def test_create_payment_intent_success(self, payment_service):
        """Test successful payment intent creation."""
        booking = BookingFactory.create(total_amount=Decimal("50.00"))
        
        # Mock Stripe payment intent creation
        payment_service.stripe_client.PaymentIntent.create = Mock(
            return_value=Mock(
                id="pi_test_123",
                client_secret="pi_test_123_secret",
                status="requires_payment_method"
            )
        )
        
        result = await payment_service.create_payment_intent(booking)
        
        assert result["payment_intent_id"] == "pi_test_123"
        assert result["client_secret"] == "pi_test_123_secret"
        payment_service.stripe_client.PaymentIntent.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_payment_success(self, payment_service):
        """Test successful payment processing."""
        payment_data = {
            "booking_id": str(uuid.uuid4()),
            "payment_intent_id": "pi_test_123",
            "amount": Decimal("50.00")
        }
        
        booking = BookingFactory.create()
        
        # Mock database operations
        payment_service.db.execute = AsyncMock()
        payment_service.db.execute.return_value.scalar_one_or_none.return_value = booking
        payment_service.db.add = Mock()
        payment_service.db.commit = AsyncMock()
        
        # Mock Stripe payment confirmation
        payment_service.stripe_client.PaymentIntent.retrieve = Mock(
            return_value=Mock(status="succeeded")
        )
        
        result = await payment_service.process_payment(payment_data)
        
        assert result is not None
        payment_service.db.add.assert_called_once()
        payment_service.db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_payment_failed(self, payment_service):
        """Test failed payment processing."""
        payment_data = {
            "booking_id": str(uuid.uuid4()),
            "payment_intent_id": "pi_test_123",
            "amount": Decimal("50.00")
        }
        
        booking = BookingFactory.create()
        
        # Mock database operations
        payment_service.db.execute = AsyncMock()
        payment_service.db.execute.return_value.scalar_one_or_none.return_value = booking
        
        # Mock Stripe payment failure
        payment_service.stripe_client.PaymentIntent.retrieve = Mock(
            return_value=Mock(status="payment_failed")
        )
        
        with pytest.raises(Exception):  # Should raise PaymentFailedException
            await payment_service.process_payment(payment_data)
    
    @pytest.mark.asyncio
    async def test_generate_receipt(self, payment_service):
        """Test receipt generation."""
        payment = PaymentFactory.create(status=PaymentStatus.COMPLETED)
        booking = BookingFactory.create()
        
        # Mock database operations
        payment_service.db.execute = AsyncMock()
        payment_service.db.execute.return_value.scalar_one_or_none.return_value = booking
        
        with patch('app.services.payment_service.generate_pdf_receipt') as mock_pdf:
            mock_pdf.return_value = b"PDF content"
            
            result = await payment_service.generate_receipt(str(payment.id))
            
            assert result is not None
            mock_pdf.assert_called_once()


class TestTrackingService:
    """Test tracking service functionality."""
    
    @pytest.fixture
    def tracking_service(self):
        """Create tracking service with mocked dependencies."""
        mock_db = AsyncMock()
        mock_websocket = Mock()
        return TrackingService(db=mock_db, websocket_manager=mock_websocket)
    
    @pytest.mark.asyncio
    async def test_update_trip_location_success(self, tracking_service):
        """Test successful trip location update."""
        trip_id = str(uuid.uuid4())
        location_data = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "speed": 65.0,
            "heading": 180.0
        }
        
        trip = TripFactory.create(status=TripStatus.IN_PROGRESS)
        
        # Mock database operations
        tracking_service.db.execute = AsyncMock()
        tracking_service.db.execute.return_value.scalar_one_or_none.return_value = trip
        tracking_service.db.add = Mock()
        tracking_service.db.commit = AsyncMock()
        
        # Mock WebSocket broadcast
        tracking_service.websocket_manager.broadcast_to_trip = AsyncMock()
        
        result = await tracking_service.update_trip_location(trip_id, location_data)
        
        assert result is not None
        tracking_service.db.add.assert_called_once()
        tracking_service.db.commit.assert_called_once()
        tracking_service.websocket_manager.broadcast_to_trip.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_trip_location_history(self, tracking_service):
        """Test retrieving trip location history."""
        trip_id = str(uuid.uuid4())
        mock_locations = [Mock() for _ in range(5)]
        
        # Mock database query
        tracking_service.db.execute = AsyncMock()
        tracking_service.db.execute.return_value.scalars.return_value.all.return_value = mock_locations
        
        result = await tracking_service.get_trip_location_history(trip_id)
        
        assert len(result) == 5
    
    @pytest.mark.asyncio
    async def test_calculate_eta(self, tracking_service):
        """Test ETA calculation."""
        trip_id = str(uuid.uuid4())
        current_location = {
            "latitude": 40.7128,
            "longitude": -74.0060
        }
        destination = {
            "latitude": 34.0522,
            "longitude": -118.2437
        }
        
        with patch('app.services.tracking_service.calculate_distance_and_time') as mock_calc:
            mock_calc.return_value = {
                "distance_km": 4500,
                "estimated_time_minutes": 300
            }
            
            result = await tracking_service.calculate_eta(trip_id, current_location, destination)
            
            assert result["estimated_arrival"] is not None
            assert result["distance_remaining_km"] == 4500
            mock_calc.assert_called_once()


class TestFleetService:
    """Test fleet service functionality."""
    
    @pytest.fixture
    def fleet_service(self):
        """Create fleet service with mocked dependencies."""
        mock_db = AsyncMock()
        return FleetService(db=mock_db)
    
    @pytest.mark.asyncio
    async def test_create_trip_success(self, fleet_service):
        """Test successful trip creation."""
        trip_data = {
            "route_id": str(uuid.uuid4()),
            "bus_id": str(uuid.uuid4()),
            "driver_id": str(uuid.uuid4()),
            "departure_time": datetime.utcnow() + timedelta(hours=2),
            "fare": Decimal("30.00")
        }
        
        # Mock database operations
        fleet_service.db.add = Mock()
        fleet_service.db.commit = AsyncMock()
        
        result = await fleet_service.create_trip(trip_data)
        
        assert result is not None
        fleet_service.db.add.assert_called_once()
        fleet_service.db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_trip_status(self, fleet_service):
        """Test trip status update."""
        trip = TripFactory.create(status=TripStatus.SCHEDULED)
        
        # Mock database operations
        fleet_service.db.execute = AsyncMock()
        fleet_service.db.execute.return_value.scalar_one_or_none.return_value = trip
        fleet_service.db.commit = AsyncMock()
        
        result = await fleet_service.update_trip_status(str(trip.id), TripStatus.IN_PROGRESS)
        
        assert result is True
        fleet_service.db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_available_buses(self, fleet_service):
        """Test retrieving available buses."""
        mock_buses = [Mock() for _ in range(3)]
        
        # Mock database query
        fleet_service.db.execute = AsyncMock()
        fleet_service.db.execute.return_value.scalars.return_value.all.return_value = mock_buses
        
        result = await fleet_service.get_available_buses()
        
        assert len(result) == 3


@pytest.mark.unit
class TestServiceErrorHandling:
    """Test service error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_auth_service_database_error(self):
        """Test auth service handling database errors."""
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("Database connection failed")
        
        auth_service = AuthService(db=mock_db, redis=Mock())
        
        with pytest.raises(Exception):
            await auth_service.authenticate_user("test@example.com", "password")
    
    @pytest.mark.asyncio
    async def test_booking_service_concurrent_booking(self):
        """Test booking service handling concurrent bookings."""
        mock_db = AsyncMock()
        booking_service = BookingService(db=mock_db, redis=Mock())
        
        # Simulate concurrent booking scenario
        booking_data = {
            "trip_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "seat_numbers": [1],
            "total_amount": Decimal("30.00")
        }
        
        trip = TripFactory.create(available_seats=1)
        mock_db.execute.return_value.scalar_one_or_none.return_value = trip
        
        # Mock seat availability check to fail (seat taken by another booking)
        with patch.object(booking_service, '_check_seat_availability', return_value=False):
            with pytest.raises(Exception):
                await booking_service.create_booking(booking_data)
    
    @pytest.mark.asyncio
    async def test_payment_service_network_timeout(self):
        """Test payment service handling network timeouts."""
        mock_db = AsyncMock()
        mock_stripe = Mock()
        mock_stripe.PaymentIntent.create.side_effect = Exception("Network timeout")
        
        payment_service = PaymentService(db=mock_db, stripe_client=mock_stripe)
        booking = BookingFactory.create()
        
        with pytest.raises(Exception):
            await payment_service.create_payment_intent(booking)


@pytest.mark.unit
class TestServiceIntegration:
    """Test service integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_booking_payment_flow(self):
        """Test complete booking and payment flow."""
        # This would test the integration between booking and payment services
        mock_db = AsyncMock()
        
        booking_service = BookingService(db=mock_db, redis=Mock())
        payment_service = PaymentService(db=mock_db, stripe_client=Mock())
        
        # Mock successful booking creation
        booking = BookingFactory.create()
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        
        # Mock successful payment processing
        payment_service.stripe_client.PaymentIntent.create = Mock(
            return_value=Mock(
                id="pi_test_123",
                client_secret="pi_test_123_secret"
            )
        )
        
        # Test the flow
        booking_data = {
            "trip_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "seat_numbers": [1],
            "total_amount": Decimal("30.00")
        }
        
        with patch.object(booking_service, 'create_booking', return_value=booking):
            created_booking = await booking_service.create_booking(booking_data)
            payment_intent = await payment_service.create_payment_intent(created_booking)
            
            assert created_booking is not None
            assert payment_intent["payment_intent_id"] == "pi_test_123"


@pytest.mark.unit
class TestServicePerformance:
    """Test service performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_booking_service_bulk_operations(self):
        """Test booking service handling bulk operations."""
        mock_db = AsyncMock()
        booking_service = BookingService(db=mock_db, redis=Mock())
        
        # Mock bulk trip search
        mock_trips = [TripFactory.create() for _ in range(100)]
        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_trips
        
        search_params = {
            "origin_terminal_id": str(uuid.uuid4()),
            "destination_terminal_id": str(uuid.uuid4()),
            "departure_date": "2024-12-25"
        }
        
        result = await booking_service.search_trips(search_params)
        
        assert len(result) == 100
        # In actual implementation, we would measure execution time
    
    @pytest.mark.asyncio
    async def test_tracking_service_high_frequency_updates(self):
        """Test tracking service handling high-frequency location updates."""
        mock_db = AsyncMock()
        mock_websocket = Mock()
        tracking_service = TrackingService(db=mock_db, websocket_manager=mock_websocket)
        
        trip_id = str(uuid.uuid4())
        trip = TripFactory.create()
        mock_db.execute.return_value.scalar_one_or_none.return_value = trip
        
        # Simulate multiple rapid location updates
        for i in range(10):
            location_data = {
                "latitude": 40.7128 + (i * 0.001),
                "longitude": -74.0060 + (i * 0.001),
                "speed": 65.0,
                "heading": 180.0
            }
            
            await tracking_service.update_trip_location(trip_id, location_data)
        
        # Verify all updates were processed
        assert mock_db.add.call_count == 10
        assert mock_db.commit.call_count == 10