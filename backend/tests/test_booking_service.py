"""
Unit tests for booking service.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.booking_service import (
    BookingService, 
    BookingNotAvailableException,
    SeatNotAvailableException,
    BookingNotFoundException
)
from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.fleet import Trip, Bus, Route, Terminal, TripStatus
from app.models.user import User, UserRole
from app.schemas.booking import (
    BookingCreate, TripSearchRequest, SeatReservationRequest,
    BookingCancellationRequest, BookingUpdate
)


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis_mock = AsyncMock()
    redis_mock.hgetall.return_value = {}
    redis_mock.keys.return_value = []
    return redis_mock


@pytest.fixture
async def booking_service(mock_db, mock_redis):
    """Create booking service with mocked dependencies."""
    service = BookingService(mock_db)
    service.redis = mock_redis
    return service


@pytest.fixture
def sample_user():
    """Create sample user."""
    return User(
        id=uuid4(),
        email="test@example.com",
        phone="+1234567890",
        password_hash="hashed_password",
        first_name="John",
        last_name="Doe",
        role=UserRole.PASSENGER,
        is_verified=True,
        is_active=True
    )


@pytest.fixture
def sample_terminal():
    """Create sample terminal."""
    return Terminal(
        id=uuid4(),
        name="Central Station",
        city="New York",
        address="123 Main St",
        latitude=Decimal("40.7128"),
        longitude=Decimal("-74.0060"),
        is_active=True
    )


@pytest.fixture
def sample_route(sample_terminal):
    """Create sample route."""
    destination_terminal = Terminal(
        id=uuid4(),
        name="North Station",
        city="Boston",
        address="456 North Ave",
        latitude=Decimal("42.3601"),
        longitude=Decimal("-71.0589"),
        is_active=True
    )
    
    return Route(
        id=uuid4(),
        origin_terminal_id=sample_terminal.id,
        destination_terminal_id=destination_terminal.id,
        origin_terminal=sample_terminal,
        destination_terminal=destination_terminal,
        distance_km=Decimal("215.5"),
        estimated_duration_minutes=240,
        base_fare=Decimal("45.00"),
        is_active=True
    )


@pytest.fixture
def sample_bus():
    """Create sample bus."""
    return Bus(
        id=uuid4(),
        license_plate="ABC123",
        model="Mercedes Sprinter",
        capacity=50,
        amenities={"wifi": True, "ac": True},
        is_active=True
    )


@pytest.fixture
def sample_trip(sample_route, sample_bus, sample_user):
    """Create sample trip."""
    return Trip(
        id=uuid4(),
        route_id=sample_route.id,
        bus_id=sample_bus.id,
        driver_id=sample_user.id,
        route=sample_route,
        bus=sample_bus,
        driver=sample_user,
        departure_time=datetime.utcnow() + timedelta(hours=4),
        arrival_time=None,
        status=TripStatus.SCHEDULED,
        fare=Decimal("45.00"),
        available_seats=48
    )


@pytest.fixture
def sample_booking(sample_user, sample_trip):
    """Create sample booking."""
    return Booking(
        id=uuid4(),
        user_id=sample_user.id,
        trip_id=sample_trip.id,
        user=sample_user,
        trip=sample_trip,
        seat_numbers=[1, 2],
        total_amount=Decimal("90.00"),
        status=BookingStatus.PENDING,
        booking_reference="ABC12345",
        payment_status=PaymentStatus.PENDING
    )


class TestBookingService:
    """Test cases for BookingService."""
    
    @pytest.mark.asyncio
    async def test_search_trips_success(self, booking_service, mock_db, sample_trip):
        """Test successful trip search."""
        # Mock database query results
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all.return_value = [sample_trip]
        mock_result.scalars.return_value = mock_scalars
        
        # Mock count query
        mock_count_result = AsyncMock()
        mock_count_result.scalar.return_value = 1
        mock_db.execute.side_effect = [mock_result, mock_count_result]
        
        search_request = TripSearchRequest(
            origin_terminal_id=sample_trip.route.origin_terminal_id,
            departure_date=datetime.utcnow().date()
        )
        
        result = await booking_service.search_trips(search_request)
        
        assert result["total"] == 1
        assert len(result["trips"]) == 1
        assert result["page"] == 1
        assert result["size"] == 20
    
    @pytest.mark.asyncio
    async def test_get_seat_availability_success(self, booking_service, mock_db, mock_redis, sample_trip):
        """Test successful seat availability check."""
        # Mock trip query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_trip
        
        # Mock booking query (no existing bookings)
        mock_booking_result = AsyncMock()
        mock_booking_scalars = AsyncMock()
        mock_booking_scalars.all.return_value = []
        mock_booking_result.scalars.return_value = mock_booking_scalars
        
        mock_db.execute.side_effect = [mock_result, mock_booking_result]
        
        # Mock Redis (no temp reservations)
        mock_redis.hgetall.return_value = {}
        
        result = await booking_service.get_seat_availability(sample_trip.id)
        
        assert result.trip_id == sample_trip.id
        assert result.total_seats == sample_trip.bus.capacity
        assert len(result.available_seats) == sample_trip.bus.capacity
        assert len(result.occupied_seats) == 0
        assert len(result.temporarily_reserved_seats) == 0
    
    @pytest.mark.asyncio
    async def test_get_seat_availability_with_occupied_seats(self, booking_service, mock_db, mock_redis, sample_trip):
        """Test seat availability with occupied seats."""
        # Mock trip query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_trip
        
        # Mock booking query with existing bookings
        mock_booking_result = AsyncMock()
        mock_booking_scalars = AsyncMock()
        mock_booking_scalars.all.return_value = [[1, 2], [3, 4]]
        mock_booking_result.scalars.return_value = mock_booking_scalars
        
        mock_db.execute.side_effect = [mock_result, mock_booking_result]
        mock_redis.hgetall.return_value = {}
        
        result = await booking_service.get_seat_availability(sample_trip.id)
        
        assert result.trip_id == sample_trip.id
        assert 1 not in result.available_seats
        assert 2 not in result.available_seats
        assert 3 not in result.available_seats
        assert 4 not in result.available_seats
        assert set(result.occupied_seats) == {1, 2, 3, 4}
    
    @pytest.mark.asyncio
    async def test_get_seat_availability_trip_not_found(self, booking_service, mock_db):
        """Test seat availability for non-existent trip."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(BookingNotFoundException):
            await booking_service.get_seat_availability(uuid4())
    
    @pytest.mark.asyncio
    async def test_reserve_seats_temporarily_success(self, booking_service, mock_redis, sample_trip, sample_user):
        """Test successful temporary seat reservation."""
        # Mock seat availability
        with patch.object(booking_service, 'get_seat_availability') as mock_availability:
            mock_availability.return_value = AsyncMock(
                available_seats=[1, 2, 3, 4, 5],
                occupied_seats=[],
                temporarily_reserved_seats=[]
            )
            
            reservation_request = SeatReservationRequest(
                trip_id=sample_trip.id,
                seat_numbers=[1, 2]
            )
            
            result = await booking_service.reserve_seats_temporarily(
                sample_user.id, 
                reservation_request
            )
            
            assert result["trip_id"] == sample_trip.id
            assert result["seats"] == [1, 2]
            assert "reservation_id" in result
            assert "expires_at" in result
            
            # Verify Redis calls
            mock_redis.hset.assert_called_once()
            mock_redis.expire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reserve_seats_temporarily_seats_not_available(self, booking_service, sample_trip, sample_user):
        """Test temporary reservation with unavailable seats."""
        # Mock seat availability with occupied seats
        with patch.object(booking_service, 'get_seat_availability') as mock_availability:
            mock_availability.return_value = AsyncMock(
                available_seats=[3, 4, 5],
                occupied_seats=[1, 2],
                temporarily_reserved_seats=[]
            )
            
            reservation_request = SeatReservationRequest(
                trip_id=sample_trip.id,
                seat_numbers=[1, 2]  # These seats are occupied
            )
            
            with pytest.raises(SeatNotAvailableException):
                await booking_service.reserve_seats_temporarily(
                    sample_user.id, 
                    reservation_request
                )
    
    @pytest.mark.asyncio
    async def test_create_booking_success(self, booking_service, mock_db, mock_redis, sample_trip, sample_user):
        """Test successful booking creation."""
        # Mock trip query
        mock_trip_result = AsyncMock()
        mock_trip_result.scalar_one_or_none.return_value = sample_trip
        
        # Mock booking reference uniqueness check
        mock_ref_result = AsyncMock()
        mock_ref_result.scalar_one_or_none.return_value = None
        
        # Mock final booking query with relationships
        mock_booking_result = AsyncMock()
        sample_booking = Booking(
            id=uuid4(),
            user_id=sample_user.id,
            trip_id=sample_trip.id,
            trip=sample_trip,
            seat_numbers=[1, 2],
            total_amount=Decimal("90.00"),
            status=BookingStatus.PENDING,
            booking_reference="ABC12345",
            payment_status=PaymentStatus.PENDING
        )
        mock_booking_result.scalar_one.return_value = sample_booking
        
        mock_db.execute.side_effect = [
            mock_trip_result,  # Trip query
            mock_ref_result,   # Reference uniqueness check
            mock_booking_result  # Final booking query
        ]
        
        # Mock seat availability
        with patch.object(booking_service, 'get_seat_availability') as mock_availability:
            mock_availability.return_value = AsyncMock(
                available_seats=[1, 2, 3, 4, 5]
            )
            
            booking_data = BookingCreate(
                trip_id=sample_trip.id,
                seat_numbers=[1, 2]
            )
            
            result = await booking_service.create_booking(sample_user.id, booking_data)
            
            assert result.trip.id == sample_trip.id
            assert result.seat_numbers == [1, 2]
            assert result.total_amount == Decimal("90.00")
            assert result.status == BookingStatus.PENDING
            
            # Verify database operations
            mock_db.add.assert_called_once()
            assert mock_db.commit.call_count == 2  # Once for booking, once for trip update
    
    @pytest.mark.asyncio
    async def test_create_booking_trip_not_found(self, booking_service, mock_db, sample_user):
        """Test booking creation with non-existent trip."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        booking_data = BookingCreate(
            trip_id=uuid4(),
            seat_numbers=[1, 2]
        )
        
        with pytest.raises(BookingNotFoundException):
            await booking_service.create_booking(sample_user.id, booking_data)
    
    @pytest.mark.asyncio
    async def test_create_booking_trip_not_bookable(self, booking_service, mock_db, sample_trip, sample_user):
        """Test booking creation with non-bookable trip."""
        # Set trip status to completed
        sample_trip.status = TripStatus.COMPLETED
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_trip
        mock_db.execute.return_value = mock_result
        
        booking_data = BookingCreate(
            trip_id=sample_trip.id,
            seat_numbers=[1, 2]
        )
        
        with pytest.raises(BookingNotAvailableException):
            await booking_service.create_booking(sample_user.id, booking_data)
    
    @pytest.mark.asyncio
    async def test_get_booking_success(self, booking_service, mock_db, sample_booking):
        """Test successful booking retrieval."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_booking
        mock_db.execute.return_value = mock_result
        
        result = await booking_service.get_booking(sample_booking.id, sample_booking.user_id)
        
        assert result.id == sample_booking.id
        assert result.booking_reference == sample_booking.booking_reference
    
    @pytest.mark.asyncio
    async def test_get_booking_not_found(self, booking_service, mock_db):
        """Test booking retrieval for non-existent booking."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(BookingNotFoundException):
            await booking_service.get_booking(uuid4(), uuid4())
    
    @pytest.mark.asyncio
    async def test_cancel_booking_success(self, booking_service, mock_db, sample_booking):
        """Test successful booking cancellation."""
        # Set departure time to be more than 2 hours away
        sample_booking.trip.departure_time = datetime.utcnow() + timedelta(hours=4)
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_booking
        mock_db.execute.return_value = mock_result
        
        cancellation_request = BookingCancellationRequest(
            reason="Change of plans"
        )
        
        result = await booking_service.cancel_booking(
            sample_booking.id,
            sample_booking.user_id,
            cancellation_request
        )
        
        assert result.status == BookingStatus.CANCELLED
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cancel_booking_too_late(self, booking_service, mock_db, sample_booking):
        """Test booking cancellation too close to departure."""
        # Set departure time to be less than 2 hours away
        sample_booking.trip.departure_time = datetime.utcnow() + timedelta(hours=1)
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_booking
        mock_db.execute.return_value = mock_result
        
        cancellation_request = BookingCancellationRequest(
            reason="Emergency"
        )
        
        with pytest.raises(BookingNotAvailableException, match="within 2 hours"):
            await booking_service.cancel_booking(
                sample_booking.id,
                sample_booking.user_id,
                cancellation_request
            )
    
    @pytest.mark.asyncio
    async def test_cancel_booking_already_cancelled(self, booking_service, mock_db, sample_booking):
        """Test cancellation of already cancelled booking."""
        sample_booking.status = BookingStatus.CANCELLED
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_booking
        mock_db.execute.return_value = mock_result
        
        cancellation_request = BookingCancellationRequest()
        
        with pytest.raises(BookingNotAvailableException, match="already cancelled"):
            await booking_service.cancel_booking(
                sample_booking.id,
                sample_booking.user_id,
                cancellation_request
            )
    
    @pytest.mark.asyncio
    async def test_update_booking_status_success(self, booking_service, mock_db, sample_booking):
        """Test successful booking status update."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_booking
        mock_db.execute.return_value = mock_result
        
        update_data = BookingUpdate(
            status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.COMPLETED
        )
        
        result = await booking_service.update_booking_status(sample_booking.id, update_data)
        
        assert result.status == BookingStatus.CONFIRMED
        assert result.payment_status == PaymentStatus.COMPLETED
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_bookings_success(self, booking_service, mock_db, sample_booking):
        """Test successful user bookings retrieval."""
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all.return_value = [sample_booking]
        mock_result.scalars.return_value = mock_scalars
        
        mock_count_result = AsyncMock()
        mock_count_result.scalar.return_value = 1
        
        mock_db.execute.side_effect = [mock_result, mock_count_result]
        
        result = await booking_service.get_user_bookings(sample_booking.user_id)
        
        assert result["total"] == 1
        assert len(result["bookings"]) == 1
        assert result["page"] == 1
        assert result["size"] == 20
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_reservations(self, booking_service, mock_redis):
        """Test cleanup of expired temporary reservations."""
        # Mock Redis keys and expired reservations
        mock_redis.keys.return_value = ["temp_reservations:trip1", "temp_reservations:trip2"]
        
        expired_reservation = {
            "user_id": str(uuid4()),
            "seats": [1, 2],
            "created_at": (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
            "expires_at": (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        }
        
        valid_reservation = {
            "user_id": str(uuid4()),
            "seats": [3, 4],
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        }
        
        import json
        mock_redis.hgetall.side_effect = [
            {"res1": json.dumps(expired_reservation), "res2": json.dumps(valid_reservation)},
            {}
        ]
        
        result = await booking_service.cleanup_expired_reservations()
        
        assert result == 1  # One expired reservation cleaned
        mock_redis.hdel.assert_called_once_with("temp_reservations:trip1", "res1")