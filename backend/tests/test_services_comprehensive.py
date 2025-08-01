"""
Comprehensive unit tests for all backend services.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.services.auth_service import AuthService
from app.services.booking_service import BookingService
from app.services.payment_service import PaymentService
from app.services.tracking_service import TrackingService
from app.services.fleet_service import FleetService
from app.services.maps_service import MapsService
from app.services.review_service import ReviewService
from app.services.admin_service import AdminService

from app.models.user import User, UserRole
from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.fleet import Terminal, Route, Bus, Trip, TripStatus
from app.models.payment import Payment, PaymentMethod
from app.models.tracking import TripLocation

from app.schemas.user import UserCreate, UserLogin
from app.schemas.booking import BookingCreate, BookingUpdate
from app.schemas.payment import PaymentCreate
from app.schemas.fleet import TripCreate, BusCreate
from app.schemas.review import ReviewCreate

from tests.factories import (
    UserFactory, BookingFactory, TripFactory, BusFactory, 
    TerminalFactory, RouteFactory, PaymentFactory
)


@pytest.mark.asyncio
class TestAuthServiceComprehensive:
    """Comprehensive tests for AuthService."""
    
    async def test_authenticate_user_success(self, db_session: AsyncSession, mock_redis):
        """Test successful user authentication."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            # Create user with known password
            user = UserFactory.create(
                email="test@example.com",
                password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # "secret"
            )
            db_session.add(user)
            await db_session.commit()
            
            # Test authentication
            authenticated_user = await auth_service.authenticate_user("test@example.com", "secret")
            
            assert authenticated_user is not None
            assert authenticated_user.email == "test@example.com"
    
    async def test_authenticate_user_invalid_credentials(self, db_session: AsyncSession, mock_redis):
        """Test authentication with invalid credentials."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            user = UserFactory.create(email="test@example.com")
            db_session.add(user)
            await db_session.commit()
            
            # Test with wrong password
            authenticated_user = await auth_service.authenticate_user("test@example.com", "wrong_password")
            assert authenticated_user is None
            
            # Test with non-existent email
            authenticated_user = await auth_service.authenticate_user("nonexistent@example.com", "password")
            assert authenticated_user is None
    
    async def test_create_access_token(self, db_session: AsyncSession, mock_redis):
        """Test access token creation."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            user = UserFactory.create()
            token = await auth_service.create_access_token(user.id)
            
            assert token is not None
            assert isinstance(token, str)
            assert len(token) > 0
    
    async def test_verify_email_token_success(self, db_session: AsyncSession, mock_redis):
        """Test successful email verification."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            user = UserFactory.create(is_verified=False)
            db_session.add(user)
            await db_session.commit()
            
            # Mock Redis to return user ID for token
            mock_redis.get = AsyncMock(return_value=str(user.id))
            
            result = await auth_service.verify_email("valid_token")
            
            assert result is True
            await db_session.refresh(user)
            assert user.is_verified is True


@pytest.mark.asyncio
class TestBookingServiceComprehensive:
    """Comprehensive tests for BookingService."""
    
    async def test_create_booking_success(self, db_session: AsyncSession, complete_test_scenario):
        """Test successful booking creation."""
        booking_service = BookingService(db_session)
        
        trip = complete_test_scenario['trips']['upcoming_trip']
        user = complete_test_scenario['users']['passenger']
        
        booking_data = BookingCreate(
            trip_id=trip.id,
            seat_numbers=[1, 2]
        )
        
        booking = await booking_service.create_booking(user.id, booking_data)
        
        assert booking.user_id == user.id
        assert booking.trip_id == trip.id
        assert booking.seat_numbers == [1, 2]
        assert booking.status == BookingStatus.PENDING
        assert booking.booking_reference is not None
    
    async def test_create_booking_no_available_seats(self, db_session: AsyncSession, complete_test_scenario):
        """Test booking creation when no seats available."""
        booking_service = BookingService(db_session)
        
        trip = complete_test_scenario['trips']['full_trip']  # Trip with 0 available seats
        user = complete_test_scenario['users']['passenger']
        
        booking_data = BookingCreate(
            trip_id=trip.id,
            seat_numbers=[1]
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await booking_service.create_booking(user.id, booking_data)
        
        assert exc_info.value.status_code == 409
        assert "not available" in str(exc_info.value.detail).lower()
    
    async def test_cancel_booking_success(self, db_session: AsyncSession, complete_test_scenario):
        """Test successful booking cancellation."""
        booking_service = BookingService(db_session)
        
        booking = complete_test_scenario['bookings']['confirmed_booking']
        
        cancelled_booking = await booking_service.cancel_booking(booking.id, booking.user_id)
        
        assert cancelled_booking.status == BookingStatus.CANCELLED
    
    async def test_get_user_bookings(self, db_session: AsyncSession, complete_test_scenario):
        """Test retrieving user bookings."""
        booking_service = BookingService(db_session)
        
        user = complete_test_scenario['users']['passenger']
        
        bookings = await booking_service.get_user_bookings(user.id)
        
        assert len(bookings) > 0
        assert all(booking.user_id == user.id for booking in bookings)


@pytest.mark.asyncio
class TestPaymentServiceComprehensive:
    """Comprehensive tests for PaymentService."""
    
    async def test_create_payment_intent_success(self, db_session: AsyncSession, complete_test_scenario):
        """Test successful payment intent creation."""
        with patch('stripe.PaymentIntent.create') as mock_stripe:
            mock_stripe.return_value = MagicMock(
                id='pi_test_123',
                client_secret='pi_test_123_secret',
                amount=5000,
                currency='usd'
            )
            
            payment_service = PaymentService(db_session)
            booking = complete_test_scenario['bookings']['pending_booking']
            
            payment_data = PaymentCreate(
                booking_id=booking.id,
                payment_method="card"
            )
            
            payment_intent = await payment_service.create_payment_intent(payment_data)
            
            assert payment_intent['id'] == 'pi_test_123'
            assert payment_intent['client_secret'] == 'pi_test_123_secret'
            mock_stripe.assert_called_once()
    
    async def test_confirm_payment_success(self, db_session: AsyncSession, complete_test_scenario):
        """Test successful payment confirmation."""
        with patch('stripe.PaymentIntent.retrieve') as mock_stripe:
            mock_stripe.return_value = MagicMock(
                id='pi_test_123',
                status='succeeded',
                amount=5000,
                currency='usd'
            )
            
            payment_service = PaymentService(db_session)
            booking = complete_test_scenario['bookings']['pending_booking']
            
            # Create a payment record
            payment = PaymentFactory.create(booking_id=booking.id)
            db_session.add(payment)
            await db_session.commit()
            
            confirmed_payment = await payment_service.confirm_payment('pi_test_123')
            
            assert confirmed_payment is not None
            mock_stripe.assert_called_once_with('pi_test_123')
    
    async def test_process_refund(self, db_session: AsyncSession, complete_test_scenario):
        """Test payment refund processing."""
        with patch('stripe.Refund.create') as mock_stripe:
            mock_stripe.return_value = MagicMock(
                id='re_test_123',
                status='succeeded',
                amount=5000
            )
            
            payment_service = PaymentService(db_session)
            payment = complete_test_scenario['payments']['successful_payment']
            
            refund = await payment_service.process_refund(payment.id)
            
            assert refund is not None
            mock_stripe.assert_called_once()


@pytest.mark.asyncio
class TestTrackingServiceComprehensive:
    """Comprehensive tests for TrackingService."""
    
    async def test_update_trip_location(self, db_session: AsyncSession, complete_test_scenario):
        """Test trip location update."""
        tracking_service = TrackingService(db_session)
        
        trip = complete_test_scenario['trips']['current_trip']
        
        location_data = {
            'latitude': Decimal('40.7128'),
            'longitude': Decimal('-74.0060'),
            'speed': Decimal('65.0'),
            'heading': Decimal('180.0')
        }
        
        location = await tracking_service.update_trip_location(trip.id, location_data)
        
        assert location.trip_id == trip.id
        assert location.latitude == Decimal('40.7128')
        assert location.longitude == Decimal('-74.0060')
        assert location.speed == Decimal('65.0')
        assert location.heading == Decimal('180.0')
    
    async def test_get_trip_current_location(self, db_session: AsyncSession, complete_test_scenario):
        """Test getting current trip location."""
        tracking_service = TrackingService(db_session)
        
        trip = complete_test_scenario['trips']['current_trip']
        
        # Add a location
        location_data = {
            'latitude': Decimal('40.7128'),
            'longitude': Decimal('-74.0060'),
            'speed': Decimal('65.0'),
            'heading': Decimal('180.0')
        }
        await tracking_service.update_trip_location(trip.id, location_data)
        
        current_location = await tracking_service.get_trip_current_location(trip.id)
        
        assert current_location is not None
        assert current_location.trip_id == trip.id
    
    async def test_get_trip_location_history(self, db_session: AsyncSession, complete_test_scenario):
        """Test getting trip location history."""
        tracking_service = TrackingService(db_session)
        
        trip = complete_test_scenario['trips']['current_trip']
        locations = complete_test_scenario['trip_locations']['current_trip']
        
        history = await tracking_service.get_trip_location_history(trip.id)
        
        assert len(history) > 0
        assert all(loc.trip_id == trip.id for loc in history)


@pytest.mark.asyncio
class TestFleetServiceComprehensive:
    """Comprehensive tests for FleetService."""
    
    async def test_create_trip(self, db_session: AsyncSession, complete_test_scenario):
        """Test trip creation."""
        fleet_service = FleetService(db_session)
        
        route = complete_test_scenario['routes']['ny_to_la']
        bus = complete_test_scenario['buses']['luxury_bus']
        driver = complete_test_scenario['users']['driver']
        
        trip_data = TripCreate(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id,
            departure_time=datetime.utcnow() + timedelta(hours=24),
            fare=Decimal('150.00')
        )
        
        trip = await fleet_service.create_trip(trip_data)
        
        assert trip.route_id == route.id
        assert trip.bus_id == bus.id
        assert trip.driver_id == driver.id
        assert trip.fare == Decimal('150.00')
        assert trip.status == TripStatus.SCHEDULED
    
    async def test_get_available_trips(self, db_session: AsyncSession, complete_test_scenario):
        """Test getting available trips."""
        fleet_service = FleetService(db_session)
        
        route = complete_test_scenario['routes']['ny_to_la']
        departure_date = datetime.utcnow().date()
        
        trips = await fleet_service.get_available_trips(
            origin_terminal_id=route.origin_terminal_id,
            destination_terminal_id=route.destination_terminal_id,
            departure_date=departure_date
        )
        
        assert isinstance(trips, list)
        # Should include trips that are scheduled and have available seats
    
    async def test_update_trip_status(self, db_session: AsyncSession, complete_test_scenario):
        """Test trip status update."""
        fleet_service = FleetService(db_session)
        
        trip = complete_test_scenario['trips']['upcoming_trip']
        
        updated_trip = await fleet_service.update_trip_status(trip.id, TripStatus.IN_PROGRESS)
        
        assert updated_trip.status == TripStatus.IN_PROGRESS


@pytest.mark.asyncio
class TestMapsServiceComprehensive:
    """Comprehensive tests for MapsService."""
    
    async def test_geocode_address(self):
        """Test address geocoding."""
        with patch('googlemaps.Client') as mock_client:
            mock_client.return_value.geocode.return_value = [
                {
                    'geometry': {
                        'location': {'lat': 40.7128, 'lng': -74.0060}
                    },
                    'formatted_address': '123 Broadway, New York, NY 10001, USA'
                }
            ]
            
            maps_service = MapsService()
            result = await maps_service.geocode_address("123 Broadway, New York, NY")
            
            assert result is not None
            assert result['latitude'] == 40.7128
            assert result['longitude'] == -74.0060
    
    async def test_calculate_route_distance(self):
        """Test route distance calculation."""
        with patch('googlemaps.Client') as mock_client:
            mock_client.return_value.directions.return_value = [
                {
                    'legs': [
                        {
                            'distance': {'value': 4500000, 'text': '4,500 km'},
                            'duration': {'value': 172800, 'text': '48 hours'}
                        }
                    ]
                }
            ]
            
            maps_service = MapsService()
            result = await maps_service.calculate_route_distance(
                origin=(40.7128, -74.0060),
                destination=(34.0522, -118.2437)
            )
            
            assert result is not None
            assert result['distance_km'] == 4500.0
            assert result['duration_minutes'] == 2880


@pytest.mark.asyncio
class TestReviewServiceComprehensive:
    """Comprehensive tests for ReviewService."""
    
    async def test_create_review(self, db_session: AsyncSession, complete_test_scenario):
        """Test review creation."""
        review_service = ReviewService(db_session)
        
        booking = complete_test_scenario['bookings']['confirmed_booking']
        user = complete_test_scenario['users']['passenger']
        driver = complete_test_scenario['users']['driver']
        
        review_data = ReviewCreate(
            booking_id=booking.id,
            rating=5,
            comment="Excellent service!"
        )
        
        review = await review_service.create_review(user.id, review_data)
        
        assert review.booking_id == booking.id
        assert review.user_id == user.id
        assert review.rating == 5
        assert review.comment == "Excellent service!"
    
    async def test_get_driver_reviews(self, db_session: AsyncSession, complete_test_scenario):
        """Test getting driver reviews."""
        review_service = ReviewService(db_session)
        
        driver = complete_test_scenario['users']['driver']
        
        reviews = await review_service.get_driver_reviews(driver.id)
        
        assert isinstance(reviews, list)
    
    async def test_calculate_average_rating(self, db_session: AsyncSession, complete_test_scenario):
        """Test average rating calculation."""
        review_service = ReviewService(db_session)
        
        driver = complete_test_scenario['users']['driver']
        
        # This would typically have reviews in the database
        avg_rating = await review_service.calculate_average_rating(driver.id)
        
        assert avg_rating is None or (0 <= avg_rating <= 5)


@pytest.mark.asyncio
class TestAdminServiceComprehensive:
    """Comprehensive tests for AdminService."""
    
    async def test_get_dashboard_metrics(self, db_session: AsyncSession, complete_test_scenario):
        """Test dashboard metrics retrieval."""
        admin_service = AdminService(db_session)
        
        metrics = await admin_service.get_dashboard_metrics()
        
        assert 'total_users' in metrics
        assert 'total_bookings' in metrics
        assert 'total_trips' in metrics
        assert 'revenue' in metrics
        assert isinstance(metrics['total_users'], int)
        assert isinstance(metrics['total_bookings'], int)
        assert isinstance(metrics['total_trips'], int)
    
    async def test_search_users(self, db_session: AsyncSession, complete_test_scenario):
        """Test user search functionality."""
        admin_service = AdminService(db_session)
        
        users = await admin_service.search_users(query="passenger")
        
        assert isinstance(users, list)
        # Should return users matching the search query
    
    async def test_suspend_user(self, db_session: AsyncSession, complete_test_scenario):
        """Test user suspension."""
        admin_service = AdminService(db_session)
        
        user = complete_test_scenario['users']['passenger']
        
        suspended_user = await admin_service.suspend_user(user.id)
        
        assert suspended_user.is_active is False
    
    async def test_activate_user(self, db_session: AsyncSession, complete_test_scenario):
        """Test user activation."""
        admin_service = AdminService(db_session)
        
        user = complete_test_scenario['users']['inactive_user']
        
        activated_user = await admin_service.activate_user(user.id)
        
        assert activated_user.is_active is True