"""
Unit tests for the tracking service.
"""
import pytest
import pytest_asyncio
import uuid
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.tracking_service import TrackingService
from app.models.tracking import TripLocation
from app.models.fleet import Trip, TripStatus, Route, Terminal, Bus
from app.models.booking import Booking, BookingStatus
from app.models.user import User


@pytest_asyncio.fixture
async def tracking_service(db_session: AsyncSession):
    """Create tracking service instance."""
    return TrackingService(db_session)


@pytest_asyncio.fixture
async def sample_terminal(db_session: AsyncSession):
    """Create a sample terminal."""
    terminal = Terminal(
        name="Central Station",
        city="Test City",
        address="123 Main St",
        latitude=Decimal("40.7128"),
        longitude=Decimal("-74.0060"),
        is_active=True
    )
    db_session.add(terminal)
    await db_session.commit()
    await db_session.refresh(terminal)
    return terminal


@pytest_asyncio.fixture
async def sample_route(db_session: AsyncSession, sample_terminal):
    """Create a sample route."""
    destination_terminal = Terminal(
        name="Airport Terminal",
        city="Test City",
        address="456 Airport Rd",
        latitude=Decimal("40.6892"),
        longitude=Decimal("-74.1745"),
        is_active=True
    )
    db_session.add(destination_terminal)
    await db_session.commit()
    await db_session.refresh(destination_terminal)
    
    route = Route(
        origin_terminal_id=sample_terminal.id,
        destination_terminal_id=destination_terminal.id,
        distance_km=Decimal("25.5"),
        estimated_duration_minutes=45,
        base_fare=Decimal("15.00"),
        is_active=True
    )
    db_session.add(route)
    await db_session.commit()
    await db_session.refresh(route)
    return route


@pytest_asyncio.fixture
async def sample_bus(db_session: AsyncSession):
    """Create a sample bus."""
    bus = Bus(
        license_plate="ABC-123",
        model="Mercedes Sprinter",
        capacity=20,
        amenities={"wifi": True, "ac": True},
        is_active=True
    )
    db_session.add(bus)
    await db_session.commit()
    await db_session.refresh(bus)
    return bus


@pytest_asyncio.fixture
async def sample_driver(db_session: AsyncSession):
    """Create a sample driver."""
    driver = User(
        email="driver@test.com",
        phone="+1234567890",
        password_hash="hashed_password",
        first_name="John",
        last_name="Driver",
        role="driver",
        is_verified=True,
        is_active=True
    )
    db_session.add(driver)
    await db_session.commit()
    await db_session.refresh(driver)
    return driver


@pytest_asyncio.fixture
async def sample_trip(db_session: AsyncSession, sample_route, sample_bus, sample_driver):
    """Create a sample trip."""
    trip = Trip(
        route_id=sample_route.id,
        bus_id=sample_bus.id,
        driver_id=sample_driver.id,
        departure_time=datetime.utcnow() + timedelta(hours=1),
        status=TripStatus.IN_TRANSIT,
        fare=Decimal("15.00"),
        available_seats=18
    )
    db_session.add(trip)
    await db_session.commit()
    await db_session.refresh(trip)
    return trip


@pytest_asyncio.fixture
async def sample_passenger(db_session: AsyncSession):
    """Create a sample passenger."""
    passenger = User(
        email="passenger@test.com",
        phone="+1234567891",
        password_hash="hashed_password",
        first_name="Jane",
        last_name="Passenger",
        role="passenger",
        is_verified=True,
        is_active=True
    )
    db_session.add(passenger)
    await db_session.commit()
    await db_session.refresh(passenger)
    return passenger


@pytest_asyncio.fixture
async def sample_booking(db_session: AsyncSession, sample_trip, sample_passenger):
    """Create a sample booking."""
    booking = Booking(
        user_id=sample_passenger.id,
        trip_id=sample_trip.id,
        seat_numbers=[1, 2],
        total_amount=Decimal("30.00"),
        status=BookingStatus.CONFIRMED,
        booking_reference="BK123456",
        created_at=datetime.utcnow()
    )
    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)
    return booking


class TestTrackingService:
    """Test cases for TrackingService."""
    
    @pytest.mark.asyncio
    async def test_update_trip_location_success(self, tracking_service, sample_trip):
        """Test successful trip location update."""
        with patch('app.core.redis.redis_client.setex', new_callable=AsyncMock) as mock_redis:
            location = await tracking_service.update_trip_location(
                trip_id=sample_trip.id,
                latitude=40.7589,
                longitude=-73.9851,
                speed=45.5,
                heading=180.0
            )
            
            assert location.trip_id == sample_trip.id
            assert location.latitude == Decimal("40.7589")
            assert location.longitude == Decimal("-73.9851")
            assert location.speed == Decimal("45.5")
            assert location.heading == Decimal("180.0")
            assert location.recorded_at is not None
            
            # Verify Redis cache was called
            mock_redis.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_trip_location_invalid_coordinates(self, tracking_service, sample_trip):
        """Test location update with invalid coordinates."""
        with pytest.raises(ValueError, match="Latitude must be between -90 and 90 degrees"):
            await tracking_service.update_trip_location(
                trip_id=sample_trip.id,
                latitude=95.0,  # Invalid latitude
                longitude=-73.9851
            )
        
        with pytest.raises(ValueError, match="Longitude must be between -180 and 180 degrees"):
            await tracking_service.update_trip_location(
                trip_id=sample_trip.id,
                latitude=40.7589,
                longitude=185.0  # Invalid longitude
            )
    
    @pytest.mark.asyncio
    async def test_update_trip_location_invalid_speed(self, tracking_service, sample_trip):
        """Test location update with invalid speed."""
        with pytest.raises(ValueError, match="Speed cannot be negative"):
            await tracking_service.update_trip_location(
                trip_id=sample_trip.id,
                latitude=40.7589,
                longitude=-73.9851,
                speed=-10.0  # Invalid speed
            )
    
    @pytest.mark.asyncio
    async def test_update_trip_location_invalid_heading(self, tracking_service, sample_trip):
        """Test location update with invalid heading."""
        with pytest.raises(ValueError, match="Heading must be between 0 and 360 degrees"):
            await tracking_service.update_trip_location(
                trip_id=sample_trip.id,
                latitude=40.7589,
                longitude=-73.9851,
                heading=370.0  # Invalid heading
            )
    
    @pytest.mark.asyncio
    async def test_update_trip_location_nonexistent_trip(self, tracking_service):
        """Test location update for non-existent trip."""
        fake_trip_id = uuid.uuid4()
        
        with pytest.raises(ValueError, match=f"Trip {fake_trip_id} not found"):
            await tracking_service.update_trip_location(
                trip_id=fake_trip_id,
                latitude=40.7589,
                longitude=-73.9851
            )
    
    @pytest.mark.asyncio
    async def test_update_trip_location_invalid_status(self, tracking_service, sample_trip, db_session):
        """Test location update for trip with invalid status."""
        # Change trip status to completed
        sample_trip.status = TripStatus.COMPLETED
        await db_session.commit()
        
        with pytest.raises(ValueError, match="Cannot update location for trip with status TripStatus.COMPLETED"):
            await tracking_service.update_trip_location(
                trip_id=sample_trip.id,
                latitude=40.7589,
                longitude=-73.9851
            )
    
    @pytest.mark.asyncio
    async def test_get_trip_location_from_cache(self, tracking_service, sample_trip):
        """Test getting trip location from Redis cache."""
        cached_data = {
            "trip_id": str(sample_trip.id),
            "latitude": 40.7589,
            "longitude": -73.9851,
            "speed": 45.5,
            "heading": 180.0,
            "recorded_at": datetime.utcnow().isoformat()
        }
        
        with patch('app.core.redis.redis_client.get', new_callable=AsyncMock) as mock_redis:
            mock_redis.return_value = json.dumps(cached_data)
            
            location = await tracking_service.get_trip_location(sample_trip.id)
            
            assert location["trip_id"] == str(sample_trip.id)
            assert location["latitude"] == 40.7589
            assert location["longitude"] == -73.9851
            mock_redis.assert_called_once_with(f"trip_location:{sample_trip.id}")
    
    @pytest.mark.asyncio
    async def test_get_trip_location_from_database(self, tracking_service, sample_trip, db_session):
        """Test getting trip location from database when not in cache."""
        # Create a location record
        location_record = TripLocation(
            trip_id=sample_trip.id,
            latitude=Decimal("40.7589"),
            longitude=Decimal("-73.9851"),
            speed=Decimal("45.5"),
            heading=Decimal("180.0"),
            recorded_at=datetime.utcnow()
        )
        db_session.add(location_record)
        await db_session.commit()
        
        with patch('app.core.redis.redis_client.get', new_callable=AsyncMock) as mock_redis:
            mock_redis.return_value = None  # No cache
            
            location = await tracking_service.get_trip_location(sample_trip.id)
            
            assert location["trip_id"] == str(sample_trip.id)
            assert location["latitude"] == 40.7589
            assert location["longitude"] == -73.9851
    
    @pytest.mark.asyncio
    async def test_get_trip_location_not_found(self, tracking_service):
        """Test getting location for trip with no location data."""
        fake_trip_id = uuid.uuid4()
        
        with patch('app.core.redis.redis_client.get', new_callable=AsyncMock) as mock_redis:
            mock_redis.return_value = None
            
            location = await tracking_service.get_trip_location(fake_trip_id)
            assert location is None
    
    @pytest.mark.asyncio
    async def test_get_trip_location_history(self, tracking_service, sample_trip, db_session):
        """Test getting trip location history."""
        # Create multiple location records
        locations = []
        for i in range(3):
            location = TripLocation(
                trip_id=sample_trip.id,
                latitude=Decimal(f"40.{7589 + i}"),
                longitude=Decimal(f"-73.{9851 + i}"),
                speed=Decimal(f"{45 + i}.5"),
                recorded_at=datetime.utcnow() - timedelta(minutes=i)
            )
            locations.append(location)
            db_session.add(location)
        
        await db_session.commit()
        
        history = await tracking_service.get_trip_location_history(sample_trip.id, limit=5)
        
        assert len(history) == 3
        # Should be ordered by recorded_at desc (most recent first)
        assert history[0]["latitude"] == 40.7589  # Most recent
        assert history[2]["latitude"] == 40.7591  # Oldest
    
    @pytest.mark.asyncio
    async def test_update_trip_status_success(self, tracking_service, sample_trip, sample_driver):
        """Test successful trip status update."""
        with patch('app.core.redis.redis_client.setex', new_callable=AsyncMock) as mock_redis:
            trip = await tracking_service.update_trip_status(
                trip_id=sample_trip.id,
                status=TripStatus.ARRIVED,
                driver_id=sample_driver.id
            )
            
            assert trip.status == TripStatus.ARRIVED
            mock_redis.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_trip_status_unauthorized_driver(self, tracking_service, sample_trip):
        """Test trip status update by unauthorized driver."""
        fake_driver_id = uuid.uuid4()
        
        with pytest.raises(ValueError, match="Only the assigned driver can update trip status"):
            await tracking_service.update_trip_status(
                trip_id=sample_trip.id,
                status=TripStatus.ARRIVED,
                driver_id=fake_driver_id
            )
    
    @pytest.mark.asyncio
    async def test_update_trip_status_completion_sets_arrival_time(self, tracking_service, sample_trip, sample_driver):
        """Test that completing a trip sets arrival time."""
        # Ensure arrival time is not set initially
        assert sample_trip.arrival_time is None
        
        with patch('app.core.redis.redis_client.setex', new_callable=AsyncMock):
            trip = await tracking_service.update_trip_status(
                trip_id=sample_trip.id,
                status=TripStatus.COMPLETED,
                driver_id=sample_driver.id
            )
            
            assert trip.status == TripStatus.COMPLETED
            assert trip.arrival_time is not None
    
    @pytest.mark.asyncio
    async def test_get_active_trips_for_driver(self, tracking_service, sample_driver, db_session, sample_route, sample_bus):
        """Test getting active trips for a driver."""
        # Create multiple trips with different statuses
        active_trip = Trip(
            route_id=sample_route.id,
            bus_id=sample_bus.id,
            driver_id=sample_driver.id,
            departure_time=datetime.utcnow() + timedelta(hours=1),
            status=TripStatus.SCHEDULED,
            fare=Decimal("15.00"),
            available_seats=20
        )
        
        completed_trip = Trip(
            route_id=sample_route.id,
            bus_id=sample_bus.id,
            driver_id=sample_driver.id,
            departure_time=datetime.utcnow() - timedelta(hours=2),
            status=TripStatus.COMPLETED,
            fare=Decimal("15.00"),
            available_seats=0
        )
        
        db_session.add_all([active_trip, completed_trip])
        await db_session.commit()
        
        active_trips = await tracking_service.get_active_trips_for_driver(sample_driver.id)
        
        # Should only return active trips (scheduled, boarding, in_transit)
        trip_ids = [trip.id for trip in active_trips]
        assert active_trip.id in trip_ids
        assert completed_trip.id not in trip_ids
    
    @pytest.mark.asyncio
    async def test_get_passengers_for_trip(self, tracking_service, sample_trip, sample_booking):
        """Test getting passengers for a trip."""
        passengers = await tracking_service.get_passengers_for_trip(sample_trip.id)
        
        assert len(passengers) == 1
        assert sample_booking.user_id in passengers
    
    @pytest.mark.asyncio
    async def test_calculate_distance(self, tracking_service):
        """Test distance calculation between coordinates."""
        # Distance between NYC and LA (approximately 3944 km)
        distance = tracking_service._calculate_distance(
            40.7128, -74.0060,  # NYC
            34.0522, -118.2437  # LA
        )
        
        # Should be approximately 3944 km (allow 50km tolerance)
        assert 3900 <= distance <= 4000
    
    @pytest.mark.asyncio
    async def test_geofencing_terminal_arrival(self, tracking_service, sample_trip, sample_route, db_session):
        """Test geofencing logic for terminal arrival detection."""
        # Load the route with destination terminal
        await db_session.refresh(sample_route, ["destination_terminal"])
        destination = sample_route.destination_terminal
        
        # Update location very close to destination terminal (within 100m)
        with patch('app.core.redis.redis_client.setex', new_callable=AsyncMock):
            await tracking_service.update_trip_location(
                trip_id=sample_trip.id,
                latitude=float(destination.latitude) + 0.0001,  # Very close
                longitude=float(destination.longitude) + 0.0001
            )
        
        # Refresh trip to check status
        await db_session.refresh(sample_trip)
        
        # Trip status should be updated to ARRIVED
        assert sample_trip.status == TripStatus.ARRIVED