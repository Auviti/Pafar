"""
Complete unit tests for all backend services.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.services.auth_service import AuthService
from app.services.booking_service import BookingService
from app.services.payment_service import PaymentService
from app.services.tracking_service import TrackingService
from app.services.review_service import ReviewService
from app.services.admin_service import AdminService
from app.services.maps_service import MapsService
from app.services.fleet_service import TerminalService, RouteService, BusService, TripService

from app.models.user import User, UserRole
from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus as PaymentStatusEnum
from app.models.fleet import Terminal, Route, Bus, Trip, TripStatus
from app.models.tracking import TripLocation

from app.core.exceptions import (
    ValidationError, NotFoundError, ConflictError, 
    AuthenticationError, AuthorizationError
)

from tests.factories import (
    UserFactory, BookingFactory, PaymentFactory, TripFactory,
    TerminalFactory, RouteFactory, BusFactory, TripLocationFactory
)


class TestAuthService:
    """Test AuthService functionality."""
    
    @pytest.fixture
    def auth_service(self, db_session: AsyncSession):
        return AuthService(db_session)
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, db_session):
        """Test successful user registration."""
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890"
        }
        
        user = await auth_service.register_user(**user_data)
        
        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.phone == "+1234567890"
        assert user.role == UserRole.PASSENGER
        assert not user.is_verified
        assert user.is_active
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, auth_service, db_session):
        """Test registration with duplicate email."""
        existing_user = UserFactory.create(email="test@example.com")
        db_session.add(existing_user)
        await db_session.commit()
        
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "first_name": "Jane",
            "last_name": "Doe"
        }
        
        with pytest.raises(ConflictError, match="Email already registered"):
            await auth_service.register_user(**user_data)
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, db_session):
        """Test successful user authentication."""
        user = UserFactory.create(
            email="test@example.com",
            password_hash="$2b$12$hashed_password",
            is_verified=True
        )
        db_session.add(user)
        await db_session.commit()
        
        with patch('app.core.security.verify_password', return_value=True):
            authenticated_user = await auth_service.authenticate_user(
                "test@example.com", "password123"
            )
        
        assert authenticated_user.id == user.id
        assert authenticated_user.email == user.email
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_credentials(self, auth_service, db_session):
        """Test authentication with invalid credentials."""
        user = UserFactory.create(
            email="test@example.com",
            password_hash="$2b$12$hashed_password",
            is_verified=True
        )
        db_session.add(user)
        await db_session.commit()
        
        with patch('app.core.security.verify_password', return_value=False):
            with pytest.raises(AuthenticationError, match="Invalid credentials"):
                await auth_service.authenticate_user(
                    "test@example.com", "wrongpassword"
                )
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_verified(self, auth_service, db_session):
        """Test authentication with unverified user."""
        user = UserFactory.create(
            email="test@example.com",
            password_hash="$2b$12$hashed_password",
            is_verified=False
        )
        db_session.add(user)
        await db_session.commit()
        
        with patch('app.core.security.verify_password', return_value=True):
            with pytest.raises(AuthenticationError, match="Email not verified"):
                await auth_service.authenticate_user(
                    "test@example.com", "password123"
                )
    
    @pytest.mark.asyncio
    async def test_verify_email_success(self, auth_service, db_session):
        """Test successful email verification."""
        user = UserFactory.create(is_verified=False)
        db_session.add(user)
        await db_session.commit()
        
        with patch('app.core.security.verify_token', return_value={"user_id": str(user.id)}):
            verified_user = await auth_service.verify_email("valid_token")
        
        assert verified_user.is_verified is True
    
    @pytest.mark.asyncio
    async def test_reset_password_success(self, auth_service, db_session):
        """Test successful password reset."""
        user = UserFactory.create(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        
        with patch('app.core.security.verify_token', return_value={"user_id": str(user.id)}):
            with patch('app.core.security.get_password_hash', return_value="new_hashed_password"):
                updated_user = await auth_service.reset_password("valid_token", "newpassword123")
        
        assert updated_user.password_hash == "new_hashed_password"


class TestBookingService:
    """Test BookingService functionality."""
    
    @pytest.fixture
    def booking_service(self, db_session: AsyncSession):
        return BookingService(db_session)
    
    @pytest.mark.asyncio
    async def test_create_booking_success(self, booking_service, db_session):
        """Test successful booking creation."""
        user = UserFactory.create()
        trip = TripFactory.create(available_seats=10)
        db_session.add_all([user, trip])
        await db_session.commit()
        
        booking_data = {
            "user_id": user.id,
            "trip_id": trip.id,
            "seat_numbers": [1, 2]
        }
        
        booking = await booking_service.create_booking(**booking_data)
        
        assert booking.user_id == user.id
        assert booking.trip_id == trip.id
        assert booking.seat_numbers == [1, 2]
        assert booking.status == BookingStatus.PENDING
        assert booking.booking_reference is not None
    
    @pytest.mark.asyncio
    async def test_create_booking_insufficient_seats(self, booking_service, db_session):
        """Test booking creation with insufficient seats."""
        user = UserFactory.create()
        trip = TripFactory.create(available_seats=1)
        db_session.add_all([user, trip])
        await db_session.commit()
        
        booking_data = {
            "user_id": user.id,
            "trip_id": trip.id,
            "seat_numbers": [1, 2, 3]
        }
        
        with pytest.raises(ConflictError, match="Insufficient seats available"):
            await booking_service.create_booking(**booking_data)
    
    @pytest.mark.asyncio
    async def test_confirm_booking_success(self, booking_service, db_session):
        """Test successful booking confirmation."""
        booking = BookingFactory.create(status=BookingStatus.PENDING)
        db_session.add(booking)
        await db_session.commit()
        
        confirmed_booking = await booking_service.confirm_booking(booking.id)
        
        assert confirmed_booking.status == BookingStatus.CONFIRMED
    
    @pytest.mark.asyncio
    async def test_cancel_booking_success(self, booking_service, db_session):
        """Test successful booking cancellation."""
        booking = BookingFactory.create(
            status=BookingStatus.CONFIRMED,
            created_at=datetime.utcnow() - timedelta(hours=1)
        )
        trip = TripFactory.create(
            departure_time=datetime.utcnow() + timedelta(hours=25)
        )
        booking.trip_id = trip.id
        
        db_session.add_all([booking, trip])
        await db_session.commit()
        
        cancelled_booking = await booking_service.cancel_booking(booking.id)
        
        assert cancelled_booking.status == BookingStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_cancel_booking_too_late(self, booking_service, db_session):
        """Test booking cancellation too close to departure."""
        booking = BookingFactory.create(status=BookingStatus.CONFIRMED)
        trip = TripFactory.create(
            departure_time=datetime.utcnow() + timedelta(hours=12)
        )
        booking.trip_id = trip.id
        
        db_session.add_all([booking, trip])
        await db_session.commit()
        
        with pytest.raises(ConflictError, match="Cannot cancel booking"):
            await booking_service.cancel_booking(booking.id)


class TestPaymentService:
    """Test PaymentService functionality."""
    
    @pytest.fixture
    def payment_service(self, db_session: AsyncSession):
        return PaymentService(db_session)
    
    @pytest.mark.asyncio
    async def test_create_payment_intent_success(self, payment_service, db_session):
        """Test successful payment intent creation."""
        booking = BookingFactory.create(total_amount=Decimal("50.00"))
        db_session.add(booking)
        await db_session.commit()
        
        with patch('stripe.PaymentIntent.create') as mock_stripe:
            mock_stripe.return_value = Mock(
                id="pi_test_123",
                client_secret="pi_test_123_secret",
                amount=5000,
                currency="usd",
                status="requires_payment_method"
            )
            
            payment_intent = await payment_service.create_payment_intent(
                booking.id, PaymentMethod.CARD
            )
        
        assert payment_intent["id"] == "pi_test_123"
        assert payment_intent["amount"] == 5000
        assert payment_intent["currency"] == "usd"
    
    @pytest.mark.asyncio
    async def test_process_payment_success(self, payment_service, db_session):
        """Test successful payment processing."""
        booking = BookingFactory.create()
        db_session.add(booking)
        await db_session.commit()
        
        payment_data = {
            "booking_id": booking.id,
            "amount": Decimal("50.00"),
            "payment_method": PaymentMethod.CARD,
            "gateway_transaction_id": "txn_123"
        }
        
        payment = await payment_service.process_payment(**payment_data)
        
        assert payment.booking_id == booking.id
        assert payment.amount == Decimal("50.00")
        assert payment.status == PaymentStatusEnum.COMPLETED
    
    @pytest.mark.asyncio
    async def test_refund_payment_success(self, payment_service, db_session):
        """Test successful payment refund."""
        payment = PaymentFactory.create(
            status=PaymentStatusEnum.COMPLETED,
            gateway_transaction_id="txn_123"
        )
        db_session.add(payment)
        await db_session.commit()
        
        with patch('stripe.Refund.create') as mock_stripe:
            mock_stripe.return_value = Mock(
                id="re_test_123",
                status="succeeded",
                amount=5000
            )
            
            refunded_payment = await payment_service.refund_payment(payment.id)
        
        assert refunded_payment.status == PaymentStatusEnum.REFUNDED


class TestTrackingService:
    """Test TrackingService functionality."""
    
    @pytest.fixture
    def tracking_service(self, db_session: AsyncSession):
        return TrackingService(db_session)
    
    @pytest.mark.asyncio
    async def test_update_trip_location_success(self, tracking_service, db_session):
        """Test successful trip location update."""
        trip = TripFactory.create(status=TripStatus.IN_PROGRESS)
        db_session.add(trip)
        await db_session.commit()
        
        location_data = {
            "trip_id": trip.id,
            "latitude": Decimal("40.7128"),
            "longitude": Decimal("-74.0060"),
            "speed": Decimal("65.0"),
            "heading": Decimal("180.0")
        }
        
        location = await tracking_service.update_trip_location(**location_data)
        
        assert location.trip_id == trip.id
        assert location.latitude == Decimal("40.7128")
        assert location.longitude == Decimal("-74.0060")
    
    @pytest.mark.asyncio
    async def test_get_trip_location_history(self, tracking_service, db_session):
        """Test retrieving trip location history."""
        trip = TripFactory.create()
        locations = [
            TripLocationFactory.create(trip_id=trip.id),
            TripLocationFactory.create(trip_id=trip.id),
            TripLocationFactory.create(trip_id=trip.id)
        ]
        
        db_session.add_all([trip] + locations)
        await db_session.commit()
        
        history = await tracking_service.get_trip_location_history(trip.id)
        
        assert len(history) == 3
        assert all(loc.trip_id == trip.id for loc in history)
    
    @pytest.mark.asyncio
    async def test_calculate_eta_success(self, tracking_service, db_session):
        """Test ETA calculation."""
        trip = TripFactory.create()
        current_location = TripLocationFactory.create(trip_id=trip.id)
        
        db_session.add_all([trip, current_location])
        await db_session.commit()
        
        with patch('app.services.maps_service.MapsService.calculate_route') as mock_maps:
            mock_maps.return_value = {
                "distance": 50000,  # 50km in meters
                "duration": 3600    # 1 hour in seconds
            }
            
            eta = await tracking_service.calculate_eta(trip.id)
        
        assert eta is not None
        assert isinstance(eta, datetime)


class TestReviewService:
    """Test ReviewService functionality."""
    
    @pytest.fixture
    def review_service(self, db_session: AsyncSession):
        return ReviewService(db_session)
    
    @pytest.mark.asyncio
    async def test_create_review_success(self, review_service, db_session):
        """Test successful review creation."""
        user = UserFactory.create()
        driver = UserFactory.create_driver()
        booking = BookingFactory.create(
            user_id=user.id,
            status=BookingStatus.COMPLETED
        )
        
        db_session.add_all([user, driver, booking])
        await db_session.commit()
        
        review_data = {
            "booking_id": booking.id,
            "user_id": user.id,
            "driver_id": driver.id,
            "rating": 5,
            "comment": "Excellent service!"
        }
        
        review = await review_service.create_review(**review_data)
        
        assert review.booking_id == booking.id
        assert review.rating == 5
        assert review.comment == "Excellent service!"
        assert not review.is_moderated
    
    @pytest.mark.asyncio
    async def test_create_review_invalid_rating(self, review_service, db_session):
        """Test review creation with invalid rating."""
        user = UserFactory.create()
        driver = UserFactory.create_driver()
        booking = BookingFactory.create(user_id=user.id)
        
        db_session.add_all([user, driver, booking])
        await db_session.commit()
        
        review_data = {
            "booking_id": booking.id,
            "user_id": user.id,
            "driver_id": driver.id,
            "rating": 6,  # Invalid rating
            "comment": "Test comment"
        }
        
        with pytest.raises(ValidationError, match="Rating must be between 1 and 5"):
            await review_service.create_review(**review_data)
    
    @pytest.mark.asyncio
    async def test_moderate_review_success(self, review_service, db_session):
        """Test successful review moderation."""
        from app.models.review import Review
        
        review = Review(
            id=uuid.uuid4(),
            booking_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            driver_id=uuid.uuid4(),
            rating=5,
            comment="Test comment",
            is_moderated=False,
            created_at=datetime.utcnow()
        )
        
        db_session.add(review)
        await db_session.commit()
        
        moderated_review = await review_service.moderate_review(review.id, True)
        
        assert moderated_review.is_moderated is True


class TestAdminService:
    """Test AdminService functionality."""
    
    @pytest.fixture
    def admin_service(self, db_session: AsyncSession):
        return AdminService(db_session)
    
    @pytest.mark.asyncio
    async def test_get_dashboard_metrics(self, admin_service, db_session):
        """Test dashboard metrics retrieval."""
        # Create test data
        users = [UserFactory.create() for _ in range(5)]
        trips = [TripFactory.create() for _ in range(3)]
        bookings = [BookingFactory.create() for _ in range(10)]
        
        db_session.add_all(users + trips + bookings)
        await db_session.commit()
        
        metrics = await admin_service.get_dashboard_metrics()
        
        assert "total_users" in metrics
        assert "total_trips" in metrics
        assert "total_bookings" in metrics
        assert "revenue" in metrics
    
    @pytest.mark.asyncio
    async def test_suspend_user_success(self, admin_service, db_session):
        """Test successful user suspension."""
        user = UserFactory.create(is_active=True)
        db_session.add(user)
        await db_session.commit()
        
        suspended_user = await admin_service.suspend_user(user.id)
        
        assert suspended_user.is_active is False
    
    @pytest.mark.asyncio
    async def test_activate_user_success(self, admin_service, db_session):
        """Test successful user activation."""
        user = UserFactory.create(is_active=False)
        db_session.add(user)
        await db_session.commit()
        
        activated_user = await admin_service.activate_user(user.id)
        
        assert activated_user.is_active is True


class TestMapsService:
    """Test MapsService functionality."""
    
    @pytest.fixture
    def maps_service(self):
        return MapsService()
    
    @pytest.mark.asyncio
    async def test_geocode_address_success(self, maps_service):
        """Test successful address geocoding."""
        with patch('googlemaps.Client.geocode') as mock_geocode:
            mock_geocode.return_value = [{
                'geometry': {
                    'location': {
                        'lat': 40.7128,
                        'lng': -74.0060
                    }
                },
                'formatted_address': '123 Broadway, New York, NY 10001, USA'
            }]
            
            result = await maps_service.geocode_address("123 Broadway, New York, NY")
        
        assert result['latitude'] == 40.7128
        assert result['longitude'] == -74.0060
        assert 'formatted_address' in result
    
    @pytest.mark.asyncio
    async def test_calculate_route_success(self, maps_service):
        """Test successful route calculation."""
        with patch('googlemaps.Client.directions') as mock_directions:
            mock_directions.return_value = [{
                'legs': [{
                    'distance': {'value': 50000, 'text': '50 km'},
                    'duration': {'value': 3600, 'text': '1 hour'}
                }]
            }]
            
            result = await maps_service.calculate_route(
                (40.7128, -74.0060),
                (34.0522, -118.2437)
            )
        
        assert result['distance'] == 50000
        assert result['duration'] == 3600
    
    @pytest.mark.asyncio
    async def test_search_terminals_success(self, maps_service):
        """Test successful terminal search."""
        with patch('googlemaps.Client.places_autocomplete') as mock_autocomplete:
            mock_autocomplete.return_value = [
                {
                    'description': 'New York Central Terminal',
                    'place_id': 'place_123'
                },
                {
                    'description': 'New York Bus Station',
                    'place_id': 'place_456'
                }
            ]
            
            results = await maps_service.search_terminals("New York")
        
        assert len(results) == 2
        assert results[0]['description'] == 'New York Central Terminal'


class TestFleetServices:
    """Test fleet management services."""
    
    @pytest.fixture
    def terminal_service(self, db_session: AsyncSession):
        return TerminalService(db_session)
    
    @pytest.fixture
    def route_service(self, db_session: AsyncSession):
        return RouteService(db_session)
    
    @pytest.fixture
    def bus_service(self, db_session: AsyncSession):
        return BusService(db_session)
    
    @pytest.fixture
    def trip_service(self, db_session: AsyncSession):
        return TripService(db_session)
    
    @pytest.mark.asyncio
    async def test_create_terminal_success(self, terminal_service, db_session):
        """Test successful terminal creation."""
        terminal_data = {
            "name": "Test Terminal",
            "city": "Test City",
            "address": "123 Test St",
            "latitude": Decimal("40.7128"),
            "longitude": Decimal("-74.0060")
        }
        
        terminal = await terminal_service.create_terminal(**terminal_data)
        
        assert terminal.name == "Test Terminal"
        assert terminal.city == "Test City"
        assert terminal.latitude == Decimal("40.7128")
    
    @pytest.mark.asyncio
    async def test_create_route_success(self, route_service, db_session):
        """Test successful route creation."""
        origin = TerminalFactory.create()
        destination = TerminalFactory.create()
        db_session.add_all([origin, destination])
        await db_session.commit()
        
        route_data = {
            "origin_terminal_id": origin.id,
            "destination_terminal_id": destination.id,
            "distance_km": Decimal("100.0"),
            "estimated_duration_minutes": 120,
            "base_fare": Decimal("25.00")
        }
        
        route = await route_service.create_route(**route_data)
        
        assert route.origin_terminal_id == origin.id
        assert route.destination_terminal_id == destination.id
        assert route.distance_km == Decimal("100.0")
    
    @pytest.mark.asyncio
    async def test_create_bus_success(self, bus_service, db_session):
        """Test successful bus creation."""
        bus_data = {
            "license_plate": "TEST-123",
            "model": "Test Bus Model",
            "capacity": 50,
            "amenities": {"wifi": True, "ac": True}
        }
        
        bus = await bus_service.create_bus(**bus_data)
        
        assert bus.license_plate == "TEST-123"
        assert bus.model == "Test Bus Model"
        assert bus.capacity == 50
        assert bus.amenities["wifi"] is True
    
    @pytest.mark.asyncio
    async def test_create_trip_success(self, trip_service, db_session):
        """Test successful trip creation."""
        route = RouteFactory.create()
        bus = BusFactory.create()
        driver = UserFactory.create_driver()
        
        db_session.add_all([route, bus, driver])
        await db_session.commit()
        
        trip_data = {
            "route_id": route.id,
            "bus_id": bus.id,
            "driver_id": driver.id,
            "departure_time": datetime.utcnow() + timedelta(hours=24),
            "fare": Decimal("30.00")
        }
        
        trip = await trip_service.create_trip(**trip_data)
        
        assert trip.route_id == route.id
        assert trip.bus_id == bus.id
        assert trip.driver_id == driver.id
        assert trip.fare == Decimal("30.00")
    
    @pytest.mark.asyncio
    async def test_search_trips_success(self, trip_service, db_session):
        """Test successful trip search."""
        origin = TerminalFactory.create()
        destination = TerminalFactory.create()
        route = RouteFactory.create(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id
        )
        trips = [
            TripFactory.create(
                route_id=route.id,
                departure_time=datetime.utcnow() + timedelta(hours=i*2)
            ) for i in range(3)
        ]
        
        db_session.add_all([origin, destination, route] + trips)
        await db_session.commit()
        
        search_results = await trip_service.search_trips(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id,
            departure_date=datetime.utcnow().date()
        )
        
        assert len(search_results) == 3
        assert all(trip.route_id == route.id for trip in search_results)