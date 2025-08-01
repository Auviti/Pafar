"""
Comprehensive unit tests for all database models with edge cases and validations.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.models.user import User, UserRole
from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.fleet import Terminal, Route, Bus, Trip, TripStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus as PaymentStatusEnum
from app.models.tracking import TripLocation
from tests.factories import (
    UserFactory, TerminalFactory, RouteFactory, BusFactory, TripFactory,
    BookingFactory, PaymentFactory, TripLocationFactory
)


class TestUserModelValidation:
    """Test User model validation and edge cases."""
    
    @pytest.mark.asyncio
    async def test_user_email_uniqueness(self, db_session: AsyncSession):
        """Test that user emails must be unique."""
        user1 = UserFactory.create(email="test@example.com")
        user2 = UserFactory.create(email="test@example.com")
        
        db_session.add(user1)
        await db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_user_phone_uniqueness(self, db_session: AsyncSession):
        """Test that user phone numbers must be unique when provided."""
        user1 = UserFactory.create(phone="+1234567890")
        user2 = UserFactory.create(email="different@example.com", phone="+1234567890")
        
        db_session.add(user1)
        await db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_user_full_name_property(self, db_session: AsyncSession):
        """Test user full_name property."""
        user = UserFactory.create(first_name="John", last_name="Doe")
        assert user.full_name == "John Doe"
        
        user_no_last = UserFactory.create(first_name="Jane", last_name="")
        assert user_no_last.full_name == "Jane"
    
    @pytest.mark.asyncio
    async def test_user_role_enum_validation(self, db_session: AsyncSession):
        """Test that user role must be valid enum value."""
        user = UserFactory.create(role=UserRole.ADMIN)
        db_session.add(user)
        await db_session.commit()
        
        assert user.role == UserRole.ADMIN
        assert user.role.value == "admin"
    
    @pytest.mark.asyncio
    async def test_user_default_values(self, db_session: AsyncSession):
        """Test user model default values."""
        user = UserFactory.create()
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.role == UserRole.PASSENGER
        assert user.is_verified is True  # Factory default
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None


class TestTerminalModelValidation:
    """Test Terminal model validation and edge cases."""
    
    @pytest.mark.asyncio
    async def test_terminal_coordinates_precision(self, db_session: AsyncSession):
        """Test terminal coordinate precision handling."""
        terminal = TerminalFactory.create(
            latitude=Decimal("40.12345678"),
            longitude=Decimal("-74.12345678")
        )
        
        db_session.add(terminal)
        await db_session.commit()
        await db_session.refresh(terminal)
        
        # Check precision is maintained
        assert terminal.latitude == Decimal("40.12345678")
        assert terminal.longitude == Decimal("-74.12345678")
    
    @pytest.mark.asyncio
    async def test_terminal_optional_fields(self, db_session: AsyncSession):
        """Test terminal with optional fields."""
        terminal = TerminalFactory.create(
            address=None,
            latitude=None,
            longitude=None
        )
        
        db_session.add(terminal)
        await db_session.commit()
        await db_session.refresh(terminal)
        
        assert terminal.address is None
        assert terminal.latitude is None
        assert terminal.longitude is None
    
    @pytest.mark.asyncio
    async def test_terminal_active_status(self, db_session: AsyncSession):
        """Test terminal active status functionality."""
        active_terminal = TerminalFactory.create(is_active=True)
        inactive_terminal = TerminalFactory.create(is_active=False)
        
        db_session.add_all([active_terminal, inactive_terminal])
        await db_session.commit()
        
        assert active_terminal.is_active is True
        assert inactive_terminal.is_active is False


class TestRouteModelValidation:
    """Test Route model validation and edge cases."""
    
    @pytest.mark.asyncio
    async def test_route_with_same_origin_destination(self, db_session: AsyncSession):
        """Test route validation when origin and destination are the same."""
        terminal = TerminalFactory.create()
        db_session.add(terminal)
        await db_session.commit()
        
        # This should be allowed at model level but might be validated at service level
        route = RouteFactory.create(
            origin_terminal_id=terminal.id,
            destination_terminal_id=terminal.id
        )
        
        db_session.add(route)
        await db_session.commit()
        await db_session.refresh(route)
        
        assert route.origin_terminal_id == route.destination_terminal_id
    
    @pytest.mark.asyncio
    async def test_route_decimal_precision(self, db_session: AsyncSession):
        """Test route decimal field precision."""
        origin, destination = TerminalFactory.create_pair()
        db_session.add_all([origin, destination])
        await db_session.commit()
        
        route = RouteFactory.create(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id,
            distance_km=Decimal("1234.56"),
            base_fare=Decimal("99.99")
        )
        
        db_session.add(route)
        await db_session.commit()
        await db_session.refresh(route)
        
        assert route.distance_km == Decimal("1234.56")
        assert route.base_fare == Decimal("99.99")
    
    @pytest.mark.asyncio
    async def test_route_foreign_key_constraints(self, db_session: AsyncSession):
        """Test route foreign key constraints."""
        # Try to create route with non-existent terminal IDs
        route = RouteFactory.create(
            origin_terminal_id=uuid.uuid4(),
            destination_terminal_id=uuid.uuid4()
        )
        
        db_session.add(route)
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestBusModelValidation:
    """Test Bus model validation and edge cases."""
    
    @pytest.mark.asyncio
    async def test_bus_license_plate_uniqueness(self, db_session: AsyncSession):
        """Test bus license plate uniqueness."""
        bus1 = BusFactory.create(license_plate="ABC-123")
        bus2 = BusFactory.create(license_plate="ABC-123")
        
        db_session.add(bus1)
        await db_session.commit()
        
        db_session.add(bus2)
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_bus_amenities_json_field(self, db_session: AsyncSession):
        """Test bus amenities JSON field handling."""
        complex_amenities = {
            "wifi": True,
            "ac": True,
            "charging_ports": True,
            "entertainment": {
                "tv": True,
                "movies": ["action", "comedy"],
                "music": True
            },
            "seating": {
                "reclining": True,
                "leather": False,
                "legroom": "standard"
            }
        }
        
        bus = BusFactory.create(amenities=complex_amenities)
        db_session.add(bus)
        await db_session.commit()
        await db_session.refresh(bus)
        
        assert bus.amenities == complex_amenities
        assert bus.amenities["entertainment"]["movies"] == ["action", "comedy"]
    
    @pytest.mark.asyncio
    async def test_bus_capacity_validation(self, db_session: AsyncSession):
        """Test bus capacity field."""
        bus = BusFactory.create(capacity=55)
        db_session.add(bus)
        await db_session.commit()
        await db_session.refresh(bus)
        
        assert bus.capacity == 55
        assert isinstance(bus.capacity, int)


class TestTripModelValidation:
    """Test Trip model validation and edge cases."""
    
    @pytest.mark.asyncio
    async def test_trip_datetime_handling(self, db_session: AsyncSession):
        """Test trip datetime field handling."""
        # Create required entities
        origin, destination = TerminalFactory.create_pair()
        route = RouteFactory.create(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id
        )
        bus = BusFactory.create()
        driver = UserFactory.create_driver()
        
        db_session.add_all([origin, destination, route, bus, driver])
        await db_session.commit()
        
        departure_time = datetime(2024, 6, 15, 14, 30, 0)
        arrival_time = datetime(2024, 6, 15, 18, 30, 0)
        
        trip = TripFactory.create(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id,
            departure_time=departure_time,
            arrival_time=arrival_time
        )
        
        db_session.add(trip)
        await db_session.commit()
        await db_session.refresh(trip)
        
        assert trip.departure_time == departure_time
        assert trip.arrival_time == arrival_time
    
    @pytest.mark.asyncio
    async def test_trip_status_transitions(self, db_session: AsyncSession):
        """Test trip status enum values."""
        origin, destination = TerminalFactory.create_pair()
        route = RouteFactory.create(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id
        )
        bus = BusFactory.create()
        driver = UserFactory.create_driver()
        
        db_session.add_all([origin, destination, route, bus, driver])
        await db_session.commit()
        
        trip = TripFactory.create(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id,
            status=TripStatus.SCHEDULED
        )
        
        db_session.add(trip)
        await db_session.commit()
        
        # Test status transitions
        trip.status = TripStatus.IN_PROGRESS
        await db_session.commit()
        await db_session.refresh(trip)
        assert trip.status == TripStatus.IN_PROGRESS
        
        trip.status = TripStatus.COMPLETED
        await db_session.commit()
        await db_session.refresh(trip)
        assert trip.status == TripStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_trip_available_seats_tracking(self, db_session: AsyncSession):
        """Test trip available seats field."""
        origin, destination = TerminalFactory.create_pair()
        route = RouteFactory.create(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id
        )
        bus = BusFactory.create(capacity=50)
        driver = UserFactory.create_driver()
        
        db_session.add_all([origin, destination, route, bus, driver])
        await db_session.commit()
        
        trip = TripFactory.create(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id,
            available_seats=50
        )
        
        db_session.add(trip)
        await db_session.commit()
        await db_session.refresh(trip)
        
        assert trip.available_seats == 50
        
        # Simulate booking reducing available seats
        trip.available_seats = 48
        await db_session.commit()
        await db_session.refresh(trip)
        
        assert trip.available_seats == 48


class TestBookingModelValidation:
    """Test Booking model validation and edge cases."""
    
    @pytest.mark.asyncio
    async def test_booking_reference_uniqueness(self, db_session: AsyncSession):
        """Test booking reference uniqueness."""
        # Create required entities
        user = UserFactory.create()
        origin, destination = TerminalFactory.create_pair()
        route = RouteFactory.create(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id
        )
        bus = BusFactory.create()
        driver = UserFactory.create_driver()
        trip = TripFactory.create(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id
        )
        
        db_session.add_all([user, origin, destination, route, bus, driver, trip])
        await db_session.commit()
        
        booking1 = BookingFactory.create(
            user_id=user.id,
            trip_id=trip.id,
            booking_reference="BK123456"
        )
        booking2 = BookingFactory.create(
            user_id=user.id,
            trip_id=trip.id,
            booking_reference="BK123456"
        )
        
        db_session.add(booking1)
        await db_session.commit()
        
        db_session.add(booking2)
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_booking_seat_numbers_array(self, db_session: AsyncSession):
        """Test booking seat numbers array field."""
        user = UserFactory.create()
        origin, destination = TerminalFactory.create_pair()
        route = RouteFactory.create(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id
        )
        bus = BusFactory.create()
        driver = UserFactory.create_driver()
        trip = TripFactory.create(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id
        )
        
        db_session.add_all([user, origin, destination, route, bus, driver, trip])
        await db_session.commit()
        
        booking = BookingFactory.create(
            user_id=user.id,
            trip_id=trip.id,
            seat_numbers=[1, 5, 10, 15]
        )
        
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        assert booking.seat_numbers == [1, 5, 10, 15]
        assert len(booking.seat_numbers) == 4
    
    @pytest.mark.asyncio
    async def test_booking_status_and_payment_status(self, db_session: AsyncSession):
        """Test booking status and payment status enums."""
        user = UserFactory.create()
        origin, destination = TerminalFactory.create_pair()
        route = RouteFactory.create(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id
        )
        bus = BusFactory.create()
        driver = UserFactory.create_driver()
        trip = TripFactory.create(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id
        )
        
        db_session.add_all([user, origin, destination, route, bus, driver, trip])
        await db_session.commit()
        
        booking = BookingFactory.create(
            user_id=user.id,
            trip_id=trip.id,
            status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.COMPLETED
        )
        
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        assert booking.status == BookingStatus.CONFIRMED
        assert booking.payment_status == PaymentStatus.COMPLETED


class TestPaymentModelValidation:
    """Test Payment model validation and edge cases."""
    
    @pytest.mark.asyncio
    async def test_payment_amount_precision(self, db_session: AsyncSession):
        """Test payment amount decimal precision."""
        # Create required entities
        user = UserFactory.create()
        origin, destination = TerminalFactory.create_pair()
        route = RouteFactory.create(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id
        )
        bus = BusFactory.create()
        driver = UserFactory.create_driver()
        trip = TripFactory.create(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id
        )
        booking = BookingFactory.create(
            user_id=user.id,
            trip_id=trip.id
        )
        
        db_session.add_all([user, origin, destination, route, bus, driver, trip, booking])
        await db_session.commit()
        
        payment = PaymentFactory.create(
            booking_id=booking.id,
            amount=Decimal("123.45")
        )
        
        db_session.add(payment)
        await db_session.commit()
        await db_session.refresh(payment)
        
        assert payment.amount == Decimal("123.45")
    
    @pytest.mark.asyncio
    async def test_payment_method_enum(self, db_session: AsyncSession):
        """Test payment method enum values."""
        user = UserFactory.create()
        origin, destination = TerminalFactory.create_pair()
        route = RouteFactory.create(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id
        )
        bus = BusFactory.create()
        driver = UserFactory.create_driver()
        trip = TripFactory.create(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id
        )
        booking = BookingFactory.create(
            user_id=user.id,
            trip_id=trip.id
        )
        
        db_session.add_all([user, origin, destination, route, bus, driver, trip, booking])
        await db_session.commit()
        
        # Test different payment methods
        card_payment = PaymentFactory.create(
            booking_id=booking.id,
            payment_method=PaymentMethod.CARD
        )
        
        db_session.add(card_payment)
        await db_session.commit()
        await db_session.refresh(card_payment)
        
        assert card_payment.payment_method == PaymentMethod.CARD
    
    @pytest.mark.asyncio
    async def test_payment_currency_field(self, db_session: AsyncSession):
        """Test payment currency field."""
        user = UserFactory.create()
        origin, destination = TerminalFactory.create_pair()
        route = RouteFactory.create(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id
        )
        bus = BusFactory.create()
        driver = UserFactory.create_driver()
        trip = TripFactory.create(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id
        )
        booking = BookingFactory.create(
            user_id=user.id,
            trip_id=trip.id
        )
        
        db_session.add_all([user, origin, destination, route, bus, driver, trip, booking])
        await db_session.commit()
        
        payment = PaymentFactory.create(
            booking_id=booking.id,
            currency="EUR"
        )
        
        db_session.add(payment)
        await db_session.commit()
        await db_session.refresh(payment)
        
        assert payment.currency == "EUR"


class TestTripLocationModelValidation:
    """Test TripLocation model validation and edge cases."""
    
    @pytest.mark.asyncio
    async def test_trip_location_coordinate_precision(self, db_session: AsyncSession):
        """Test trip location coordinate precision."""
        # Create required entities
        origin, destination = TerminalFactory.create_pair()
        route = RouteFactory.create(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id
        )
        bus = BusFactory.create()
        driver = UserFactory.create_driver()
        trip = TripFactory.create(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id
        )
        
        db_session.add_all([origin, destination, route, bus, driver, trip])
        await db_session.commit()
        
        location = TripLocationFactory.create(
            trip_id=trip.id,
            latitude=Decimal("40.12345678"),
            longitude=Decimal("-74.87654321"),
            speed=Decimal("65.75"),
            heading=Decimal("180.25")
        )
        
        db_session.add(location)
        await db_session.commit()
        await db_session.refresh(location)
        
        assert location.latitude == Decimal("40.12345678")
        assert location.longitude == Decimal("-74.87654321")
        assert location.speed == Decimal("65.75")
        assert location.heading == Decimal("180.25")
    
    @pytest.mark.asyncio
    async def test_trip_location_optional_fields(self, db_session: AsyncSession):
        """Test trip location with optional fields."""
        origin, destination = TerminalFactory.create_pair()
        route = RouteFactory.create(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id
        )
        bus = BusFactory.create()
        driver = UserFactory.create_driver()
        trip = TripFactory.create(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id
        )
        
        db_session.add_all([origin, destination, route, bus, driver, trip])
        await db_session.commit()
        
        location = TripLocationFactory.create(
            trip_id=trip.id,
            speed=None,
            heading=None
        )
        
        db_session.add(location)
        await db_session.commit()
        await db_session.refresh(location)
        
        assert location.speed is None
        assert location.heading is None
        assert location.recorded_at is not None
    
    @pytest.mark.asyncio
    async def test_trip_location_timestamp_handling(self, db_session: AsyncSession):
        """Test trip location timestamp handling."""
        origin, destination = TerminalFactory.create_pair()
        route = RouteFactory.create(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id
        )
        bus = BusFactory.create()
        driver = UserFactory.create_driver()
        trip = TripFactory.create(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id
        )
        
        db_session.add_all([origin, destination, route, bus, driver, trip])
        await db_session.commit()
        
        specific_time = datetime(2024, 6, 15, 14, 30, 45)
        location = TripLocationFactory.create(
            trip_id=trip.id,
            recorded_at=specific_time
        )
        
        db_session.add(location)
        await db_session.commit()
        await db_session.refresh(location)
        
        assert location.recorded_at == specific_time
    
    async def test_user_role_validation(self, db_session: AsyncSession):
        """Test user role enumeration validation."""
        passenger = UserFactory.create(role=UserRole.PASSENGER)
        driver = UserFactory.create(role=UserRole.DRIVER, email="driver@example.com")
        admin = UserFactory.create(role=UserRole.ADMIN, email="admin@example.com")
        
        db_session.add_all([passenger, driver, admin])
        await db_session.commit()
        
        assert passenger.role == UserRole.PASSENGER
        assert driver.role == UserRole.DRIVER
        assert admin.role == UserRole.ADMIN
    
    @pytest.mark.asyncio
    async def test_user_full_name_property(self, db_session: AsyncSession):
        """Test user full name property."""
        user = UserFactory.create(first_name="John", last_name="Doe")
        
        assert user.full_name == "John Doe"
    
    @pytest.mark.asyncio
    async def test_user_default_values(self, db_session: AsyncSession):
        """Test user model default values."""
        user = User(
            email="defaults@example.com",
            password_hash="hashed_password",
            first_name="Test",
            last_name="User"
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.role == UserRole.PASSENGER
        assert user.is_verified is False
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None


class TestTerminalModelValidation:
    """Test Terminal model validation and edge cases."""
    
    @pytest.mark.asyncio
    async def test_terminal_coordinate_precision(self, db_session: AsyncSession):
        """Test terminal coordinate decimal precision."""
        terminal = TerminalFactory.create(
            latitude=Decimal("40.12345678"),  # 8 decimal places
            longitude=Decimal("-73.12345678")  # 8 decimal places
        )
        
        db_session.add(terminal)
        await db_session.commit()
        await db_session.refresh(terminal)
        
        assert terminal.latitude == Decimal("40.12345678")
        assert terminal.longitude == Decimal("-73.12345678")
    
    @pytest.mark.asyncio
    async def test_terminal_required_fields(self, db_session: AsyncSession):
        """Test terminal required fields."""
        terminal = Terminal(
            name="Test Terminal",
            city="Test City"
        )
        
        db_session.add(terminal)
        await db_session.commit()
        await db_session.refresh(terminal)
        
        assert terminal.name == "Test Terminal"
        assert terminal.city == "Test City"
        assert terminal.is_active is True  # Default value
        assert terminal.created_at is not None


class TestRouteModelValidation:
    """Test Route model validation and edge cases."""
    
    @pytest.mark.asyncio
    async def test_route_distance_precision(self, db_session: AsyncSession):
        """Test route distance decimal precision."""
        origin, destination = TerminalFactory.create_pair()
        db_session.add_all([origin, destination])
        await db_session.commit()
        
        route = RouteFactory.create(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id,
            distance_km=Decimal("1234.56"),
            base_fare=Decimal("99.99")
        )
        
        db_session.add(route)
        await db_session.commit()
        await db_session.refresh(route)
        
        assert route.distance_km == Decimal("1234.56")
        assert route.base_fare == Decimal("99.99")
    
    @pytest.mark.asyncio
    async def test_route_terminal_relationships(self, db_session: AsyncSession):
        """Test route terminal foreign key relationships."""
        origin, destination = TerminalFactory.create_pair()
        db_session.add_all([origin, destination])
        await db_session.commit()
        
        route = RouteFactory.create(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id
        )
        
        db_session.add(route)
        await db_session.commit()
        await db_session.refresh(route)
        
        assert route.origin_terminal_id == origin.id
        assert route.destination_terminal_id == destination.id


class TestBusModelValidation:
    """Test Bus model validation and edge cases."""
    
    @pytest.mark.asyncio
    async def test_bus_license_plate_uniqueness(self, db_session: AsyncSession):
        """Test that bus license plates must be unique."""
        bus1 = BusFactory.create(license_plate="UNIQUE-123")
        bus2 = BusFactory.create(license_plate="UNIQUE-123")
        
        db_session.add(bus1)
        await db_session.commit()
        
        db_session.add(bus2)
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_bus_amenities_json_field(self, db_session: AsyncSession):
        """Test bus amenities JSON field functionality."""
        amenities = {
            "wifi": True,
            "ac": False,
            "charging_ports": True,
            "entertainment": False,
            "reclining_seats": True,
            "restroom": True,
            "wheelchair_accessible": False,
            "pet_friendly": True
        }
        
        bus = BusFactory.create(amenities=amenities)
        
        db_session.add(bus)
        await db_session.commit()
        await db_session.refresh(bus)
        
        assert bus.amenities == amenities
        assert bus.amenities["wifi"] is True
        assert bus.amenities["ac"] is False
        assert bus.amenities["pet_friendly"] is True
    
    @pytest.mark.asyncio
    async def test_bus_capacity_validation(self, db_session: AsyncSession):
        """Test bus capacity field."""
        bus = BusFactory.create(capacity=55)
        
        db_session.add(bus)
        await db_session.commit()
        await db_session.refresh(bus)
        
        assert bus.capacity == 55
        assert isinstance(bus.capacity, int)


class TestTripModelValidation:
    """Test Trip model validation and edge cases."""
    
    @pytest.mark.asyncio
    async def test_trip_status_enum_validation(self, db_session: AsyncSession):
        """Test trip status enumeration."""
        route = RouteFactory.create()
        bus = BusFactory.create()
        driver = UserFactory.create_driver()
        
        db_session.add_all([route, bus, driver])
        await db_session.commit()
        
        for status in TripStatus:
            trip = TripFactory.create(
                route_id=route.id,
                bus_id=bus.id,
                driver_id=driver.id,
                status=status
            )
            
            db_session.add(trip)
            await db_session.commit()
            await db_session.refresh(trip)
            
            assert trip.status == status
            
            # Clean up for next iteration
            await db_session.delete(trip)
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_trip_fare_precision(self, db_session: AsyncSession):
        """Test trip fare decimal precision."""
        route = RouteFactory.create()
        bus = BusFactory.create()
        driver = UserFactory.create_driver()
        
        db_session.add_all([route, bus, driver])
        await db_session.commit()
        
        trip = TripFactory.create(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id,
            fare=Decimal("125.99")
        )
        
        db_session.add(trip)
        await db_session.commit()
        await db_session.refresh(trip)
        
        assert trip.fare == Decimal("125.99")
    
    @pytest.mark.asyncio
    async def test_trip_datetime_fields(self, db_session: AsyncSession):
        """Test trip datetime fields."""
        route = RouteFactory.create()
        bus = BusFactory.create()
        driver = UserFactory.create_driver()
        
        db_session.add_all([route, bus, driver])
        await db_session.commit()
        
        departure_time = datetime.utcnow() + timedelta(hours=24)
        arrival_time = departure_time + timedelta(hours=8)
        
        trip = TripFactory.create(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id,
            departure_time=departure_time,
            arrival_time=arrival_time
        )
        
        db_session.add(trip)
        await db_session.commit()
        await db_session.refresh(trip)
        
        assert trip.departure_time == departure_time
        assert trip.arrival_time == arrival_time


class TestBookingModelValidation:
    """Test Booking model validation and edge cases."""
    
    @pytest.mark.asyncio
    async def test_booking_reference_uniqueness(self, db_session: AsyncSession):
        """Test that booking references must be unique."""
        user = UserFactory.create()
        trip = TripFactory.create()
        
        db_session.add_all([user, trip])
        await db_session.commit()
        
        booking1 = BookingFactory.create(
            user_id=user.id,
            trip_id=trip.id,
            booking_reference="UNIQUE123"
        )
        booking2 = BookingFactory.create(
            user_id=user.id,
            trip_id=trip.id,
            booking_reference="UNIQUE123"
        )
        
        db_session.add(booking1)
        await db_session.commit()
        
        db_session.add(booking2)
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_booking_seat_numbers_array(self, db_session: AsyncSession):
        """Test booking seat numbers array field."""
        user = UserFactory.create()
        trip = TripFactory.create()
        
        db_session.add_all([user, trip])
        await db_session.commit()
        
        # Test single seat
        single_seat_booking = BookingFactory.create(
            user_id=user.id,
            trip_id=trip.id,
            seat_numbers=[15],
            booking_reference="SINGLE123"
        )
        
        # Test multiple seats
        multiple_seats_booking = BookingFactory.create(
            user_id=user.id,
            trip_id=trip.id,
            seat_numbers=[1, 2, 3, 4, 5],
            booking_reference="MULTIPLE123"
        )
        
        db_session.add_all([single_seat_booking, multiple_seats_booking])
        await db_session.commit()
        
        await db_session.refresh(single_seat_booking)
        await db_session.refresh(multiple_seats_booking)
        
        assert single_seat_booking.seat_numbers == [15]
        assert multiple_seats_booking.seat_numbers == [1, 2, 3, 4, 5]
        assert len(multiple_seats_booking.seat_numbers) == 5
    
    @pytest.mark.asyncio
    async def test_booking_status_enum_validation(self, db_session: AsyncSession):
        """Test booking status enumeration."""
        user = UserFactory.create()
        trip = TripFactory.create()
        
        db_session.add_all([user, trip])
        await db_session.commit()
        
        for status in BookingStatus:
            booking = BookingFactory.create(
                user_id=user.id,
                trip_id=trip.id,
                status=status,
                booking_reference=f"STATUS_{status.value}"
            )
            
            db_session.add(booking)
            await db_session.commit()
            await db_session.refresh(booking)
            
            assert booking.status == status
            
            # Clean up for next iteration
            await db_session.delete(booking)
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_booking_payment_status_enum_validation(self, db_session: AsyncSession):
        """Test booking payment status enumeration."""
        user = UserFactory.create()
        trip = TripFactory.create()
        
        db_session.add_all([user, trip])
        await db_session.commit()
        
        for payment_status in PaymentStatus:
            booking = BookingFactory.create(
                user_id=user.id,
                trip_id=trip.id,
                payment_status=payment_status,
                booking_reference=f"PAY_{payment_status.value}"
            )
            
            db_session.add(booking)
            await db_session.commit()
            await db_session.refresh(booking)
            
            assert booking.payment_status == payment_status
            
            # Clean up for next iteration
            await db_session.delete(booking)
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_booking_total_amount_precision(self, db_session: AsyncSession):
        """Test booking total amount decimal precision."""
        user = UserFactory.create()
        trip = TripFactory.create()
        
        db_session.add_all([user, trip])
        await db_session.commit()
        
        booking = BookingFactory.create(
            user_id=user.id,
            trip_id=trip.id,
            total_amount=Decimal("375.99")
        )
        
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        assert booking.total_amount == Decimal("375.99")


class TestPaymentModelValidation:
    """Test Payment model validation and edge cases."""
    
    @pytest.mark.asyncio
    async def test_payment_method_enum_validation(self, db_session: AsyncSession):
        """Test payment method enumeration."""
        booking = BookingFactory.create()
        db_session.add(booking)
        await db_session.commit()
        
        for method in PaymentMethod:
            payment = PaymentFactory.create(
                booking_id=booking.id,
                payment_method=method,
                gateway_transaction_id=f"txn_{method.value}"
            )
            
            db_session.add(payment)
            await db_session.commit()
            await db_session.refresh(payment)
            
            assert payment.payment_method == method
            
            # Clean up for next iteration
            await db_session.delete(payment)
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_payment_status_enum_validation(self, db_session: AsyncSession):
        """Test payment status enumeration."""
        booking = BookingFactory.create()
        db_session.add(booking)
        await db_session.commit()
        
        for status in PaymentStatusEnum:
            payment = PaymentFactory.create(
                booking_id=booking.id,
                status=status,
                gateway_transaction_id=f"txn_{status.value}"
            )
            
            db_session.add(payment)
            await db_session.commit()
            await db_session.refresh(payment)
            
            assert payment.status == status
            
            # Clean up for next iteration
            await db_session.delete(payment)
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_payment_amount_precision(self, db_session: AsyncSession):
        """Test payment amount decimal precision."""
        booking = BookingFactory.create()
        db_session.add(booking)
        await db_session.commit()
        
        payment = PaymentFactory.create(
            booking_id=booking.id,
            amount=Decimal("125.99")
        )
        
        db_session.add(payment)
        await db_session.commit()
        await db_session.refresh(payment)
        
        assert payment.amount == Decimal("125.99")
    
    @pytest.mark.asyncio
    async def test_payment_currency_field(self, db_session: AsyncSession):
        """Test payment currency field."""
        booking = BookingFactory.create()
        db_session.add(booking)
        await db_session.commit()
        
        usd_payment = PaymentFactory.create(
            booking_id=booking.id,
            currency="USD",
            gateway_transaction_id="usd_txn"
        )
        
        eur_payment = PaymentFactory.create(
            booking_id=booking.id,
            currency="EUR",
            gateway_transaction_id="eur_txn"
        )
        
        db_session.add_all([usd_payment, eur_payment])
        await db_session.commit()
        
        await db_session.refresh(usd_payment)
        await db_session.refresh(eur_payment)
        
        assert usd_payment.currency == "USD"
        assert eur_payment.currency == "EUR"


class TestTripLocationModelValidation:
    """Test TripLocation model validation and edge cases."""
    
    @pytest.mark.asyncio
    async def test_trip_location_coordinate_precision(self, db_session: AsyncSession):
        """Test trip location coordinate precision."""
        trip = TripFactory.create()
        db_session.add(trip)
        await db_session.commit()
        
        location = TripLocationFactory.create(
            trip_id=trip.id,
            latitude=Decimal("40.12345678"),  # 8 decimal places
            longitude=Decimal("-74.12345678"),  # 8 decimal places
            speed=Decimal("123.45"),  # 2 decimal places
            heading=Decimal("359.99")  # 2 decimal places
        )
        
        db_session.add(location)
        await db_session.commit()
        await db_session.refresh(location)
        
        assert location.latitude == Decimal("40.12345678")
        assert location.longitude == Decimal("-74.12345678")
        assert location.speed == Decimal("123.45")
        assert location.heading == Decimal("359.99")
    
    @pytest.mark.asyncio
    async def test_trip_location_optional_fields(self, db_session: AsyncSession):
        """Test trip location with optional fields."""
        trip = TripFactory.create()
        db_session.add(trip)
        await db_session.commit()
        
        # Location with minimal required fields
        minimal_location = TripLocation(
            trip_id=trip.id,
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060")
        )
        
        db_session.add(minimal_location)
        await db_session.commit()
        await db_session.refresh(minimal_location)
        
        assert minimal_location.trip_id == trip.id
        assert minimal_location.latitude == Decimal("40.7128")
        assert minimal_location.longitude == Decimal("-74.0060")
        assert minimal_location.speed is None
        assert minimal_location.heading is None
        assert minimal_location.recorded_at is not None  # Should have default
    
    @pytest.mark.asyncio
    async def test_trip_location_recorded_at_default(self, db_session: AsyncSession):
        """Test trip location recorded_at default value."""
        trip = TripFactory.create()
        db_session.add(trip)
        await db_session.commit()
        
        before_creation = datetime.utcnow()
        
        location = TripLocation(
            trip_id=trip.id,
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060")
        )
        
        db_session.add(location)
        await db_session.commit()
        await db_session.refresh(location)
        
        after_creation = datetime.utcnow()
        
        assert before_creation <= location.recorded_at <= after_creation


class TestModelRelationships:
    """Test relationships between models."""
    
    @pytest.mark.asyncio
    async def test_user_booking_relationship(self, db_session: AsyncSession):
        """Test relationship between User and Booking models."""
        user = UserFactory.create()
        trip = TripFactory.create()
        
        db_session.add_all([user, trip])
        await db_session.commit()
        
        booking1 = BookingFactory.create(
            user_id=user.id,
            trip_id=trip.id,
            booking_reference="REL001"
        )
        booking2 = BookingFactory.create(
            user_id=user.id,
            trip_id=trip.id,
            booking_reference="REL002"
        )
        
        db_session.add_all([booking1, booking2])
        await db_session.commit()
        
        # Query user's bookings
        from sqlalchemy import select
        result = await db_session.execute(
            select(Booking).where(Booking.user_id == user.id)
        )
        user_bookings = result.scalars().all()
        
        assert len(user_bookings) == 2
        assert all(booking.user_id == user.id for booking in user_bookings)
    
    @pytest.mark.asyncio
    async def test_trip_booking_relationship(self, db_session: AsyncSession):
        """Test relationship between Trip and Booking models."""
        user = UserFactory.create()
        trip = TripFactory.create()
        
        db_session.add_all([user, trip])
        await db_session.commit()
        
        booking1 = BookingFactory.create(
            user_id=user.id,
            trip_id=trip.id,
            booking_reference="TRIP001"
        )
        booking2 = BookingFactory.create(
            user_id=user.id,
            trip_id=trip.id,
            booking_reference="TRIP002"
        )
        
        db_session.add_all([booking1, booking2])
        await db_session.commit()
        
        # Query trip's bookings
        from sqlalchemy import select
        result = await db_session.execute(
            select(Booking).where(Booking.trip_id == trip.id)
        )
        trip_bookings = result.scalars().all()
        
        assert len(trip_bookings) == 2
        assert all(booking.trip_id == trip.id for booking in trip_bookings)
    
    @pytest.mark.asyncio
    async def test_booking_payment_relationship(self, db_session: AsyncSession):
        """Test relationship between Booking and Payment models."""
        user = UserFactory.create()
        trip = TripFactory.create()
        booking = BookingFactory.create(user_id=user.id, trip_id=trip.id)
        
        db_session.add_all([user, trip, booking])
        await db_session.commit()
        
        payment = PaymentFactory.create(booking_id=booking.id)
        
        db_session.add(payment)
        await db_session.commit()
        
        # Query booking's payment
        from sqlalchemy import select
        result = await db_session.execute(
            select(Payment).where(Payment.booking_id == booking.id)
        )
        booking_payment = result.scalar_one_or_none()
        
        assert booking_payment is not None
        assert booking_payment.booking_id == booking.id
    
    @pytest.mark.asyncio
    async def test_trip_location_relationship(self, db_session: AsyncSession):
        """Test relationship between Trip and TripLocation models."""
        trip = TripFactory.create()
        db_session.add(trip)
        await db_session.commit()
        
        location1 = TripLocationFactory.create(
            trip_id=trip.id,
            recorded_at=datetime.utcnow() - timedelta(minutes=30)
        )
        location2 = TripLocationFactory.create(
            trip_id=trip.id,
            recorded_at=datetime.utcnow() - timedelta(minutes=15)
        )
        location3 = TripLocationFactory.create(
            trip_id=trip.id,
            recorded_at=datetime.utcnow()
        )
        
        db_session.add_all([location1, location2, location3])
        await db_session.commit()
        
        # Query trip's locations
        from sqlalchemy import select
        result = await db_session.execute(
            select(TripLocation)
            .where(TripLocation.trip_id == trip.id)
            .order_by(TripLocation.recorded_at)
        )
        trip_locations = result.scalars().all()
        
        assert len(trip_locations) == 3
        assert all(location.trip_id == trip.id for location in trip_locations)
        # Verify they're ordered by time
        assert trip_locations[0].recorded_at < trip_locations[1].recorded_at < trip_locations[2].recorded_at


class TestModelConstraints:
    """Test model constraints and edge cases."""
    
    @pytest.mark.asyncio
    async def test_foreign_key_constraints(self, db_session: AsyncSession):
        """Test foreign key constraints are enforced."""
        # Try to create booking with non-existent user_id
        invalid_booking = Booking(
            user_id=uuid.uuid4(),  # Non-existent user
            trip_id=uuid.uuid4(),  # Non-existent trip
            seat_numbers=[1],
            total_amount=Decimal("100.00"),
            booking_reference="INVALID123"
        )
        
        db_session.add(invalid_booking)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_not_null_constraints(self, db_session: AsyncSession):
        """Test NOT NULL constraints are enforced."""
        # Try to create user without required fields
        invalid_user = User()  # Missing required fields
        
        db_session.add(invalid_user)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_decimal_field_precision(self, db_session: AsyncSession):
        """Test decimal field precision limits."""
        user = UserFactory.create()
        trip = TripFactory.create()
        
        db_session.add_all([user, trip])
        await db_session.commit()
        
        # Test very precise decimal values
        booking = BookingFactory.create(
            user_id=user.id,
            trip_id=trip.id,
            total_amount=Decimal("999999.99")  # Maximum precision
        )
        
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        assert booking.total_amount == Decimal("999999.99")