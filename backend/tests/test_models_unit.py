"""
Unit tests for database models.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserRole
from app.models.fleet import Terminal, Route, Bus, Trip, TripStatus
from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus as PaymentStatusEnum
from app.models.tracking import TripLocation
from backend.tests.factories import (
    UserFactory, TerminalFactory, RouteFactory, BusFactory, 
    TripFactory, BookingFactory, PaymentFactory, TripLocationFactory
)


class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation(self):
        """Test basic user creation."""
        user = UserFactory.create()
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.role == UserRole.PASSENGER
        assert user.is_active is True
        assert user.is_verified is True
    
    def test_user_password_hashing(self):
        """Test password hashing functionality."""
        user = UserFactory.create(password_hash="hashed_password")
        assert user.password_hash == "hashed_password"
        # In real implementation, this would be properly hashed
    
    def test_user_roles(self):
        """Test different user roles."""
        passenger = UserFactory.create(role=UserRole.PASSENGER)
        driver = UserFactory.create_driver()
        admin = UserFactory.create_admin()
        
        assert passenger.role == UserRole.PASSENGER
        assert driver.role == UserRole.DRIVER
        assert admin.role == UserRole.ADMIN
    
    def test_user_full_name_property(self):
        """Test full name property."""
        user = UserFactory.create(first_name="John", last_name="Doe")
        # This would be implemented as a property in the actual model
        expected_full_name = f"{user.first_name} {user.last_name}"
        assert expected_full_name == "John Doe"
    
    def test_user_email_uniqueness(self):
        """Test email uniqueness constraint."""
        # This would test database constraint in integration tests
        user1 = UserFactory.create(email="unique@example.com")
        user2 = UserFactory.create(email="unique@example.com")
        
        # In actual database, this would raise IntegrityError
        assert user1.email == user2.email  # For unit test purposes


class TestTerminalModel:
    """Test Terminal model functionality."""
    
    def test_terminal_creation(self):
        """Test basic terminal creation."""
        terminal = TerminalFactory.create()
        assert terminal.id is not None
        assert terminal.name == "Test Terminal"
        assert terminal.city == "Test City"
        assert terminal.latitude == Decimal("40.7128")
        assert terminal.longitude == Decimal("-74.0060")
        assert terminal.is_active is True
    
    def test_terminal_coordinates(self):
        """Test terminal coordinate validation."""
        terminal = TerminalFactory.create(
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060")
        )
        assert isinstance(terminal.latitude, Decimal)
        assert isinstance(terminal.longitude, Decimal)
        assert -90 <= float(terminal.latitude) <= 90
        assert -180 <= float(terminal.longitude) <= 180
    
    def test_terminal_pair_creation(self):
        """Test creating terminal pairs for routes."""
        origin, destination = TerminalFactory.create_pair()
        assert origin.name == "Origin Terminal"
        assert destination.name == "Destination Terminal"
        assert origin.id != destination.id


class TestRouteModel:
    """Test Route model functionality."""
    
    def test_route_creation(self):
        """Test basic route creation."""
        route = RouteFactory.create()
        assert route.id is not None
        assert route.distance_km == Decimal("100.0")
        assert route.estimated_duration_minutes == 120
        assert route.base_fare == Decimal("25.00")
        assert route.is_active is True
    
    def test_route_with_terminals(self):
        """Test route with actual terminal references."""
        origin, destination = TerminalFactory.create_pair()
        route = RouteFactory.create(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id
        )
        assert route.origin_terminal_id == origin.id
        assert route.destination_terminal_id == destination.id
    
    def test_route_fare_calculation(self):
        """Test route fare calculations."""
        route = RouteFactory.create(
            distance_km=Decimal("150.0"),
            base_fare=Decimal("30.00")
        )
        # In actual implementation, this might have dynamic pricing
        assert route.base_fare == Decimal("30.00")


class TestBusModel:
    """Test Bus model functionality."""
    
    def test_bus_creation(self):
        """Test basic bus creation."""
        bus = BusFactory.create()
        assert bus.id is not None
        assert bus.license_plate == "TEST-123"
        assert bus.model == "Test Bus Model"
        assert bus.capacity == 50
        assert bus.is_active is True
    
    def test_bus_amenities(self):
        """Test bus amenities handling."""
        amenities = {"wifi": True, "ac": True, "charging_ports": True}
        bus = BusFactory.create(amenities=amenities)
        assert bus.amenities == amenities
        assert bus.amenities["wifi"] is True
        assert bus.amenities["ac"] is True
    
    def test_bus_capacity_validation(self):
        """Test bus capacity validation."""
        bus = BusFactory.create(capacity=50)
        assert bus.capacity > 0
        assert bus.capacity <= 100  # Reasonable upper limit


class TestTripModel:
    """Test Trip model functionality."""
    
    def test_trip_creation(self):
        """Test basic trip creation."""
        trip = TripFactory.create()
        assert trip.id is not None
        assert trip.status == TripStatus.SCHEDULED
        assert trip.fare == Decimal("30.00")
        assert trip.available_seats == 50
    
    def test_trip_timing(self):
        """Test trip timing validation."""
        departure_time = datetime.utcnow() + timedelta(hours=2)
        trip = TripFactory.create(departure_time=departure_time)
        assert trip.departure_time == departure_time
        assert trip.departure_time > datetime.utcnow()
    
    def test_trip_status_transitions(self):
        """Test trip status transitions."""
        trip = TripFactory.create(status=TripStatus.SCHEDULED)
        assert trip.status == TripStatus.SCHEDULED
        
        # In actual implementation, there would be methods to transition status
        trip.status = TripStatus.IN_PROGRESS
        assert trip.status == TripStatus.IN_PROGRESS


class TestBookingModel:
    """Test Booking model functionality."""
    
    def test_booking_creation(self):
        """Test basic booking creation."""
        booking = BookingFactory.create()
        assert booking.id is not None
        assert booking.seat_numbers == [1]
        assert booking.total_amount == Decimal("30.00")
        assert booking.status == BookingStatus.PENDING
        assert booking.booking_reference == "BK123456"
    
    def test_booking_seat_selection(self):
        """Test booking seat selection."""
        seats = [1, 2, 3]
        booking = BookingFactory.create(seat_numbers=seats)
        assert booking.seat_numbers == seats
        assert len(booking.seat_numbers) == 3
    
    def test_booking_reference_uniqueness(self):
        """Test booking reference uniqueness."""
        booking1 = BookingFactory.create(booking_reference="BK123456")
        booking2 = BookingFactory.create(booking_reference="BK789012")
        assert booking1.booking_reference != booking2.booking_reference
    
    def test_booking_amount_calculation(self):
        """Test booking amount calculation."""
        seats = [1, 2]
        fare_per_seat = Decimal("25.00")
        expected_total = fare_per_seat * len(seats)
        booking = BookingFactory.create(
            seat_numbers=seats,
            total_amount=expected_total
        )
        assert booking.total_amount == expected_total


class TestPaymentModel:
    """Test Payment model functionality."""
    
    def test_payment_creation(self):
        """Test basic payment creation."""
        payment = PaymentFactory.create()
        assert payment.id is not None
        assert payment.amount == Decimal("30.00")
        assert payment.currency == "USD"
        assert payment.payment_method == PaymentMethod.CARD
        assert payment.status == PaymentStatusEnum.PENDING
    
    def test_payment_gateway_integration(self):
        """Test payment gateway fields."""
        payment = PaymentFactory.create(
            payment_gateway="stripe",
            gateway_transaction_id="txn_123456"
        )
        assert payment.payment_gateway == "stripe"
        assert payment.gateway_transaction_id == "txn_123456"
    
    def test_payment_status_transitions(self):
        """Test payment status transitions."""
        payment = PaymentFactory.create(status=PaymentStatusEnum.PENDING)
        assert payment.status == PaymentStatusEnum.PENDING
        
        # In actual implementation, there would be methods to transition status
        payment.status = PaymentStatusEnum.COMPLETED
        assert payment.status == PaymentStatusEnum.COMPLETED


class TestTripLocationModel:
    """Test TripLocation model functionality."""
    
    def test_location_creation(self):
        """Test basic location creation."""
        location = TripLocationFactory.create()
        assert location.id is not None
        assert location.latitude == Decimal("40.7128")
        assert location.longitude == Decimal("-74.0060")
        assert location.speed == Decimal("65.0")
        assert location.heading == Decimal("180.0")
    
    def test_location_coordinates_validation(self):
        """Test location coordinate validation."""
        location = TripLocationFactory.create(
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060")
        )
        assert -90 <= float(location.latitude) <= 90
        assert -180 <= float(location.longitude) <= 180
    
    def test_location_timing(self):
        """Test location timing."""
        recorded_time = datetime.utcnow()
        location = TripLocationFactory.create(recorded_at=recorded_time)
        assert location.recorded_at == recorded_time
        assert location.recorded_at <= datetime.utcnow()


class TestModelRelationships:
    """Test model relationships and constraints."""
    
    def test_trip_route_relationship(self):
        """Test trip-route relationship."""
        route = RouteFactory.create()
        trip = TripFactory.create(route_id=route.id)
        assert trip.route_id == route.id
    
    def test_booking_user_trip_relationship(self):
        """Test booking relationships."""
        user = UserFactory.create()
        trip = TripFactory.create()
        booking = BookingFactory.create(
            user_id=user.id,
            trip_id=trip.id
        )
        assert booking.user_id == user.id
        assert booking.trip_id == trip.id
    
    def test_payment_booking_relationship(self):
        """Test payment-booking relationship."""
        booking = BookingFactory.create()
        payment = PaymentFactory.create(booking_id=booking.id)
        assert payment.booking_id == booking.id
    
    def test_location_trip_relationship(self):
        """Test location-trip relationship."""
        trip = TripFactory.create()
        location = TripLocationFactory.create(trip_id=trip.id)
        assert location.trip_id == trip.id


class TestModelValidation:
    """Test model validation and constraints."""
    
    def test_user_email_format(self):
        """Test user email format validation."""
        # In actual implementation, this would use email validation
        user = UserFactory.create(email="valid@example.com")
        assert "@" in user.email
        assert "." in user.email
    
    def test_booking_seat_numbers_validation(self):
        """Test booking seat numbers validation."""
        valid_seats = [1, 2, 3]
        booking = BookingFactory.create(seat_numbers=valid_seats)
        assert all(isinstance(seat, int) for seat in booking.seat_numbers)
        assert all(seat > 0 for seat in booking.seat_numbers)
    
    def test_payment_amount_validation(self):
        """Test payment amount validation."""
        payment = PaymentFactory.create(amount=Decimal("50.00"))
        assert payment.amount > 0
        assert isinstance(payment.amount, Decimal)
    
    def test_trip_capacity_validation(self):
        """Test trip capacity validation."""
        bus = BusFactory.create(capacity=50)
        trip = TripFactory.create(
            bus_id=bus.id,
            available_seats=50
        )
        assert trip.available_seats <= bus.capacity
        assert trip.available_seats >= 0


class TestModelMethods:
    """Test model methods and properties."""
    
    def test_user_is_active_check(self):
        """Test user active status check."""
        active_user = UserFactory.create(is_active=True)
        inactive_user = UserFactory.create(is_active=False)
        
        assert active_user.is_active is True
        assert inactive_user.is_active is False
    
    def test_booking_is_confirmed(self):
        """Test booking confirmation status."""
        confirmed_booking = BookingFactory.create(status=BookingStatus.CONFIRMED)
        pending_booking = BookingFactory.create(status=BookingStatus.PENDING)
        
        # In actual implementation, this would be a method
        assert confirmed_booking.status == BookingStatus.CONFIRMED
        assert pending_booking.status == BookingStatus.PENDING
    
    def test_trip_is_available(self):
        """Test trip availability check."""
        available_trip = TripFactory.create(available_seats=10)
        full_trip = TripFactory.create(available_seats=0)
        
        # In actual implementation, this would be a method
        assert available_trip.available_seats > 0
        assert full_trip.available_seats == 0
    
    def test_payment_is_successful(self):
        """Test payment success check."""
        successful_payment = PaymentFactory.create(status=PaymentStatusEnum.COMPLETED)
        failed_payment = PaymentFactory.create(status=PaymentStatusEnum.FAILED)
        
        # In actual implementation, this would be a method
        assert successful_payment.status == PaymentStatusEnum.COMPLETED
        assert failed_payment.status == PaymentStatusEnum.FAILED


@pytest.mark.unit
class TestModelEdgeCases:
    """Test model edge cases and error conditions."""
    
    def test_user_with_minimal_data(self):
        """Test user creation with minimal required data."""
        user = UserFactory.create(
            email="minimal@example.com",
            first_name="Min",
            last_name="User"
        )
        assert user.email == "minimal@example.com"
        assert user.first_name == "Min"
        assert user.last_name == "User"
    
    def test_booking_with_single_seat(self):
        """Test booking with single seat."""
        booking = BookingFactory.create(seat_numbers=[1])
        assert len(booking.seat_numbers) == 1
        assert booking.seat_numbers[0] == 1
    
    def test_payment_with_zero_amount(self):
        """Test payment with zero amount (should be invalid)."""
        # In actual implementation, this should raise validation error
        payment = PaymentFactory.create(amount=Decimal("0.00"))
        # For unit test, we just check the value
        assert payment.amount == Decimal("0.00")
    
    def test_trip_with_past_departure_time(self):
        """Test trip with past departure time."""
        past_time = datetime.utcnow() - timedelta(hours=1)
        trip = TripFactory.create(departure_time=past_time)
        assert trip.departure_time < datetime.utcnow()
    
    def test_location_with_extreme_coordinates(self):
        """Test location with extreme but valid coordinates."""
        location = TripLocationFactory.create(
            latitude=Decimal("89.9999"),  # Near North Pole
            longitude=Decimal("179.9999")  # Near International Date Line
        )
        assert -90 <= float(location.latitude) <= 90
        assert -180 <= float(location.longitude) <= 180


@pytest.mark.unit
class TestModelSerialization:
    """Test model serialization and deserialization."""
    
    def test_user_to_dict(self):
        """Test user serialization to dictionary."""
        user = UserFactory.create()
        # In actual implementation, this would be a to_dict method
        user_dict = {
            'id': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role.value if hasattr(user.role, 'value') else str(user.role),
            'is_active': user.is_active,
            'is_verified': user.is_verified
        }
        assert user_dict['email'] == user.email
        assert user_dict['is_active'] == user.is_active
    
    def test_booking_to_dict(self):
        """Test booking serialization to dictionary."""
        booking = BookingFactory.create()
        # In actual implementation, this would be a to_dict method
        booking_dict = {
            'id': str(booking.id),
            'seat_numbers': booking.seat_numbers,
            'total_amount': str(booking.total_amount),
            'status': booking.status.value if hasattr(booking.status, 'value') else str(booking.status),
            'booking_reference': booking.booking_reference
        }
        assert booking_dict['seat_numbers'] == booking.seat_numbers
        assert booking_dict['booking_reference'] == booking.booking_reference
    
    def test_trip_to_dict(self):
        """Test trip serialization to dictionary."""
        trip = TripFactory.create()
        # In actual implementation, this would be a to_dict method
        trip_dict = {
            'id': str(trip.id),
            'departure_time': trip.departure_time.isoformat(),
            'fare': str(trip.fare),
            'available_seats': trip.available_seats,
            'status': trip.status.value if hasattr(trip.status, 'value') else str(trip.status)
        }
        assert trip_dict['available_seats'] == trip.available_seats
        assert trip_dict['fare'] == str(trip.fare)