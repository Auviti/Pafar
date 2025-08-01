"""
Unit tests for database models.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole
from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.fleet import Terminal, Route, Bus, Trip, TripStatus
from app.models.payment import Payment, PaymentMethod
from app.models.tracking import TripLocation


class TestUserModel:
    """Test cases for User model."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a new user."""
        user = User(
            email="test@example.com",
            phone="+1234567890",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe",
            role=UserRole.PASSENGER
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "John Doe"
        assert user.role == UserRole.PASSENGER
        assert user.is_verified is False
        assert user.is_active is True
        assert user.created_at is not None
    
    @pytest.mark.asyncio
    async def test_user_relationships(self, db_session: AsyncSession):
        """Test user model relationships."""
        user = User(
            email="driver@example.com",
            password_hash="hashed_password",
            first_name="Jane",
            last_name="Driver",
            role=UserRole.DRIVER
        )
        
        db_session.add(user)
        await db_session.commit()
        
        # Test that relationships are properly defined
        assert hasattr(user, 'bookings')
        assert hasattr(user, 'driven_trips')
        assert hasattr(user, 'reviews_given')
        assert hasattr(user, 'reviews_received')


class TestTerminalModel:
    """Test cases for Terminal model."""
    
    @pytest.mark.asyncio
    async def test_create_terminal(self, db_session: AsyncSession):
        """Test creating a new terminal."""
        terminal = Terminal(
            name="Central Station",
            city="New York",
            address="123 Main St",
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060")
        )
        
        db_session.add(terminal)
        await db_session.commit()
        await db_session.refresh(terminal)
        
        assert terminal.id is not None
        assert terminal.name == "Central Station"
        assert terminal.city == "New York"
        assert terminal.latitude == Decimal("40.7128")
        assert terminal.is_active is True


class TestRouteModel:
    """Test cases for Route model."""
    
    @pytest.mark.asyncio
    async def test_create_route(self, db_session: AsyncSession):
        """Test creating a new route."""
        # Create terminals first
        origin = Terminal(
            name="Origin Terminal",
            city="City A",
            latitude=Decimal("40.0000"),
            longitude=Decimal("-74.0000")
        )
        destination = Terminal(
            name="Destination Terminal",
            city="City B",
            latitude=Decimal("41.0000"),
            longitude=Decimal("-75.0000")
        )
        
        db_session.add_all([origin, destination])
        await db_session.commit()
        
        route = Route(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id,
            distance_km=Decimal("100.5"),
            estimated_duration_minutes=120,
            base_fare=Decimal("25.00")
        )
        
        db_session.add(route)
        await db_session.commit()
        await db_session.refresh(route)
        
        assert route.id is not None
        assert route.distance_km == Decimal("100.5")
        assert route.base_fare == Decimal("25.00")
        assert route.is_active is True


class TestBusModel:
    """Test cases for Bus model."""
    
    @pytest.mark.asyncio
    async def test_create_bus(self, db_session: AsyncSession):
        """Test creating a new bus."""
        bus = Bus(
            license_plate="ABC-123",
            model="Mercedes Sprinter",
            capacity=50,
            amenities={"wifi": True, "ac": True, "charging_ports": True}
        )
        
        db_session.add(bus)
        await db_session.commit()
        await db_session.refresh(bus)
        
        assert bus.id is not None
        assert bus.license_plate == "ABC-123"
        assert bus.capacity == 50
        assert bus.amenities["wifi"] is True
        assert bus.is_active is True


class TestTripModel:
    """Test cases for Trip model."""
    
    @pytest.mark.asyncio
    async def test_create_trip(self, db_session: AsyncSession):
        """Test creating a new trip."""
        # Create required entities
        origin = Terminal(name="Origin", city="City A")
        destination = Terminal(name="Destination", city="City B")
        route = Route(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id,
            base_fare=Decimal("25.00")
        )
        bus = Bus(license_plate="BUS-001", capacity=50)
        driver = User(
            email="driver@example.com",
            password_hash="hash",
            first_name="Driver",
            last_name="One",
            role=UserRole.DRIVER
        )
        
        db_session.add_all([origin, destination])
        await db_session.commit()
        
        route.origin_terminal_id = origin.id
        route.destination_terminal_id = destination.id
        db_session.add_all([route, bus, driver])
        await db_session.commit()
        
        trip = Trip(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id,
            departure_time=datetime.utcnow() + timedelta(hours=2),
            fare=Decimal("30.00"),
            available_seats=50
        )
        
        db_session.add(trip)
        await db_session.commit()
        await db_session.refresh(trip)
        
        assert trip.id is not None
        assert trip.fare == Decimal("30.00")
        assert trip.status == TripStatus.SCHEDULED
        assert trip.available_seats == 50


class TestBookingModel:
    """Test cases for Booking model."""
    
    @pytest.mark.asyncio
    async def test_create_booking(self, db_session: AsyncSession):
        """Test creating a new booking."""
        # Create required entities (simplified)
        user = User(
            email="passenger@example.com",
            password_hash="hash",
            first_name="Passenger",
            last_name="One"
        )
        
        # Create minimal trip setup
        origin = Terminal(name="Origin", city="City A")
        destination = Terminal(name="Destination", city="City B")
        db_session.add_all([origin, destination])
        await db_session.commit()
        
        route = Route(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id,
            base_fare=Decimal("25.00")
        )
        bus = Bus(license_plate="BUS-001", capacity=50)
        driver = User(
            email="driver@example.com",
            password_hash="hash",
            first_name="Driver",
            last_name="One",
            role=UserRole.DRIVER
        )
        
        db_session.add_all([route, bus, driver, user])
        await db_session.commit()
        
        trip = Trip(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id,
            departure_time=datetime.utcnow() + timedelta(hours=2),
            fare=Decimal("30.00"),
            available_seats=50
        )
        
        db_session.add(trip)
        await db_session.commit()
        
        booking = Booking(
            user_id=user.id,
            trip_id=trip.id,
            seat_numbers=[1, 2],
            total_amount=Decimal("60.00"),
            booking_reference="BK123456"
        )
        
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        assert booking.id is not None
        assert booking.seat_numbers == [1, 2]
        assert booking.total_amount == Decimal("60.00")
        assert booking.status == BookingStatus.PENDING
        assert booking.payment_status == PaymentStatus.PENDING


class TestPaymentModel:
    """Test cases for Payment model."""
    
    @pytest.mark.asyncio
    async def test_create_payment(self, db_session: AsyncSession):
        """Test creating a new payment."""
        # Create minimal booking setup
        user = User(
            email="passenger@example.com",
            password_hash="hash",
            first_name="Passenger",
            last_name="One"
        )
        
        origin = Terminal(name="Origin", city="City A")
        destination = Terminal(name="Destination", city="City B")
        db_session.add_all([origin, destination, user])
        await db_session.commit()
        
        route = Route(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id,
            base_fare=Decimal("25.00")
        )
        bus = Bus(license_plate="BUS-001", capacity=50)
        driver = User(
            email="driver@example.com",
            password_hash="hash",
            first_name="Driver",
            last_name="One",
            role=UserRole.DRIVER
        )
        
        db_session.add_all([route, bus, driver])
        await db_session.commit()
        
        trip = Trip(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id,
            departure_time=datetime.utcnow() + timedelta(hours=2),
            fare=Decimal("30.00"),
            available_seats=50
        )
        
        db_session.add(trip)
        await db_session.commit()
        
        booking = Booking(
            user_id=user.id,
            trip_id=trip.id,
            seat_numbers=[1],
            total_amount=Decimal("30.00"),
            booking_reference="BK123456"
        )
        
        db_session.add(booking)
        await db_session.commit()
        
        payment = Payment(
            booking_id=booking.id,
            amount=Decimal("30.00"),
            currency="USD",
            payment_method=PaymentMethod.CARD,
            payment_gateway="stripe",
            gateway_transaction_id="txn_123456"
        )
        
        db_session.add(payment)
        await db_session.commit()
        await db_session.refresh(payment)
        
        assert payment.id is not None
        assert payment.amount == Decimal("30.00")
        assert payment.currency == "USD"
        assert payment.payment_method == PaymentMethod.CARD


class TestTripLocationModel:
    """Test cases for TripLocation model."""
    
    @pytest.mark.asyncio
    async def test_create_trip_location(self, db_session: AsyncSession):
        """Test creating a trip location record."""
        # Create minimal trip setup
        origin = Terminal(name="Origin", city="City A")
        destination = Terminal(name="Destination", city="City B")
        db_session.add_all([origin, destination])
        await db_session.commit()
        
        route = Route(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id,
            base_fare=Decimal("25.00")
        )
        bus = Bus(license_plate="BUS-001", capacity=50)
        driver = User(
            email="driver@example.com",
            password_hash="hash",
            first_name="Driver",
            last_name="One",
            role=UserRole.DRIVER
        )
        
        db_session.add_all([route, bus, driver])
        await db_session.commit()
        
        trip = Trip(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id,
            departure_time=datetime.utcnow() + timedelta(hours=2),
            fare=Decimal("30.00"),
            available_seats=50
        )
        
        db_session.add(trip)
        await db_session.commit()
        
        location = TripLocation(
            trip_id=trip.id,
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060"),
            speed=Decimal("65.5"),
            heading=Decimal("180.0")
        )
        
        db_session.add(location)
        await db_session.commit()
        await db_session.refresh(location)
        
        assert location.id is not None
        assert location.latitude == Decimal("40.7128")
        assert location.longitude == Decimal("-74.0060")
        assert location.speed == Decimal("65.5")
        assert location.recorded_at is not None