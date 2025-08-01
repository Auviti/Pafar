"""
Test fixtures for common testing scenarios.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole
from app.models.fleet import Terminal, Route, Bus, Trip, TripStatus
from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus as PaymentStatusEnum
from app.models.tracking import TripLocation
from tests.factories import (
    UserFactory, TerminalFactory, RouteFactory, BusFactory, TripFactory,
    BookingFactory, PaymentFactory, TripLocationFactory, TestDataBuilder
)


@pytest.fixture
async def sample_users(db_session: AsyncSession) -> Dict[str, User]:
    """Create sample users for testing."""
    users = {
        'passenger': UserFactory.create(
            email="passenger@example.com",
            first_name="John",
            last_name="Passenger",
            role=UserRole.PASSENGER
        ),
        'driver': UserFactory.create_driver(
            email="driver@example.com",
            first_name="Jane",
            last_name="Driver"
        ),
        'admin': UserFactory.create_admin(
            email="admin@example.com",
            first_name="Admin",
            last_name="User"
        ),
        'inactive_user': UserFactory.create(
            email="inactive@example.com",
            first_name="Inactive",
            last_name="User",
            is_active=False
        ),
        'unverified_user': UserFactory.create(
            email="unverified@example.com",
            first_name="Unverified",
            last_name="User",
            is_verified=False
        )
    }
    
    db_session.add_all(users.values())
    await db_session.commit()
    
    for user in users.values():
        await db_session.refresh(user)
    
    return users


@pytest.fixture
async def sample_terminals(db_session: AsyncSession) -> Dict[str, Terminal]:
    """Create sample terminals for testing."""
    terminals = {
        'new_york': TerminalFactory.create(
            name="New York Central Terminal",
            city="New York",
            address="123 Broadway, New York, NY 10001",
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060")
        ),
        'los_angeles': TerminalFactory.create(
            name="Los Angeles Union Terminal",
            city="Los Angeles",
            address="456 Main St, Los Angeles, CA 90012",
            latitude=Decimal("34.0522"),
            longitude=Decimal("-118.2437")
        ),
        'chicago': TerminalFactory.create(
            name="Chicago Central Station",
            city="Chicago",
            address="789 State St, Chicago, IL 60601",
            latitude=Decimal("41.8781"),
            longitude=Decimal("-87.6298")
        ),
        'inactive_terminal': TerminalFactory.create(
            name="Inactive Terminal",
            city="Inactive City",
            is_active=False
        )
    }
    
    db_session.add_all(terminals.values())
    await db_session.commit()
    
    for terminal in terminals.values():
        await db_session.refresh(terminal)
    
    return terminals


@pytest.fixture
async def sample_routes(db_session: AsyncSession, sample_terminals: Dict[str, Terminal]) -> Dict[str, Route]:
    """Create sample routes for testing."""
    routes = {
        'ny_to_la': RouteFactory.create(
            origin_terminal_id=sample_terminals['new_york'].id,
            destination_terminal_id=sample_terminals['los_angeles'].id,
            distance_km=Decimal("4500.0"),
            estimated_duration_minutes=2880,  # 48 hours
            base_fare=Decimal("150.00")
        ),
        'ny_to_chicago': RouteFactory.create(
            origin_terminal_id=sample_terminals['new_york'].id,
            destination_terminal_id=sample_terminals['chicago'].id,
            distance_km=Decimal("1200.0"),
            estimated_duration_minutes=720,  # 12 hours
            base_fare=Decimal("75.00")
        ),
        'chicago_to_la': RouteFactory.create(
            origin_terminal_id=sample_terminals['chicago'].id,
            destination_terminal_id=sample_terminals['los_angeles'].id,
            distance_km=Decimal("3200.0"),
            estimated_duration_minutes=1920,  # 32 hours
            base_fare=Decimal("120.00")
        ),
        'inactive_route': RouteFactory.create(
            origin_terminal_id=sample_terminals['new_york'].id,
            destination_terminal_id=sample_terminals['inactive_terminal'].id,
            is_active=False
        )
    }
    
    db_session.add_all(routes.values())
    await db_session.commit()
    
    for route in routes.values():
        await db_session.refresh(route)
    
    return routes


@pytest.fixture
async def sample_buses(db_session: AsyncSession) -> Dict[str, Bus]:
    """Create sample buses for testing."""
    buses = {
        'luxury_bus': BusFactory.create(
            license_plate="LUX-001",
            model="Mercedes-Benz Tourismo",
            capacity=55,
            amenities={
                "wifi": True,
                "ac": True,
                "charging_ports": True,
                "entertainment": True,
                "reclining_seats": True,
                "restroom": True
            }
        ),
        'standard_bus': BusFactory.create(
            license_plate="STD-002",
            model="Volvo 9700",
            capacity=50,
            amenities={
                "wifi": True,
                "ac": True,
                "charging_ports": True,
                "entertainment": False,
                "reclining_seats": False,
                "restroom": True
            }
        ),
        'economy_bus': BusFactory.create(
            license_plate="ECO-003",
            model="Setra S 416 LE",
            capacity=45,
            amenities={
                "wifi": False,
                "ac": True,
                "charging_ports": False,
                "entertainment": False,
                "reclining_seats": False,
                "restroom": False
            }
        ),
        'inactive_bus': BusFactory.create(
            license_plate="INA-004",
            model="Inactive Bus",
            capacity=40,
            is_active=False
        )
    }
    
    db_session.add_all(buses.values())
    await db_session.commit()
    
    for bus in buses.values():
        await db_session.refresh(bus)
    
    return buses


@pytest.fixture
async def sample_trips(
    db_session: AsyncSession,
    sample_routes: Dict[str, Route],
    sample_buses: Dict[str, Bus],
    sample_users: Dict[str, User]
) -> Dict[str, Trip]:
    """Create sample trips for testing."""
    base_time = datetime.utcnow()
    
    trips = {
        'upcoming_trip': TripFactory.create(
            route_id=sample_routes['ny_to_la'].id,
            bus_id=sample_buses['luxury_bus'].id,
            driver_id=sample_users['driver'].id,
            departure_time=base_time + timedelta(hours=24),
            arrival_time=base_time + timedelta(hours=72),
            status=TripStatus.SCHEDULED,
            fare=Decimal("175.00"),
            available_seats=50
        ),
        'current_trip': TripFactory.create(
            route_id=sample_routes['ny_to_chicago'].id,
            bus_id=sample_buses['standard_bus'].id,
            driver_id=sample_users['driver'].id,
            departure_time=base_time - timedelta(hours=2),
            arrival_time=base_time + timedelta(hours=10),
            status=TripStatus.IN_PROGRESS,
            fare=Decimal("85.00"),
            available_seats=30
        ),
        'completed_trip': TripFactory.create(
            route_id=sample_routes['chicago_to_la'].id,
            bus_id=sample_buses['economy_bus'].id,
            driver_id=sample_users['driver'].id,
            departure_time=base_time - timedelta(days=2),
            arrival_time=base_time - timedelta(days=1),
            status=TripStatus.COMPLETED,
            fare=Decimal("130.00"),
            available_seats=0
        ),
        'cancelled_trip': TripFactory.create(
            route_id=sample_routes['ny_to_la'].id,
            bus_id=sample_buses['standard_bus'].id,
            driver_id=sample_users['driver'].id,
            departure_time=base_time + timedelta(hours=48),
            status=TripStatus.CANCELLED,
            fare=Decimal("175.00"),
            available_seats=50
        ),
        'full_trip': TripFactory.create(
            route_id=sample_routes['ny_to_chicago'].id,
            bus_id=sample_buses['economy_bus'].id,
            driver_id=sample_users['driver'].id,
            departure_time=base_time + timedelta(hours=36),
            fare=Decimal("85.00"),
            available_seats=0  # Fully booked
        )
    }
    
    db_session.add_all(trips.values())
    await db_session.commit()
    
    for trip in trips.values():
        await db_session.refresh(trip)
    
    return trips


@pytest.fixture
async def sample_bookings(
    db_session: AsyncSession,
    sample_users: Dict[str, User],
    sample_trips: Dict[str, Trip]
) -> Dict[str, Booking]:
    """Create sample bookings for testing."""
    bookings = {
        'confirmed_booking': BookingFactory.create(
            user_id=sample_users['passenger'].id,
            trip_id=sample_trips['upcoming_trip'].id,
            seat_numbers=[1, 2],
            total_amount=Decimal("350.00"),
            status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.COMPLETED,
            booking_reference="BK001234"
        ),
        'pending_booking': BookingFactory.create(
            user_id=sample_users['passenger'].id,
            trip_id=sample_trips['current_trip'].id,
            seat_numbers=[5],
            total_amount=Decimal("85.00"),
            status=BookingStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            booking_reference="BK001235"
        ),
        'cancelled_booking': BookingFactory.create(
            user_id=sample_users['passenger'].id,
            trip_id=sample_trips['completed_trip'].id,
            seat_numbers=[10, 11],
            total_amount=Decimal("260.00"),
            status=BookingStatus.CANCELLED,
            payment_status=PaymentStatus.REFUNDED,
            booking_reference="BK001236"
        ),
        'failed_payment_booking': BookingFactory.create(
            user_id=sample_users['passenger'].id,
            trip_id=sample_trips['upcoming_trip'].id,
            seat_numbers=[15],
            total_amount=Decimal("175.00"),
            status=BookingStatus.PENDING,
            payment_status=PaymentStatus.FAILED,
            booking_reference="BK001237"
        )
    }
    
    db_session.add_all(bookings.values())
    await db_session.commit()
    
    for booking in bookings.values():
        await db_session.refresh(booking)
    
    return bookings


@pytest.fixture
async def sample_payments(
    db_session: AsyncSession,
    sample_bookings: Dict[str, Booking]
) -> Dict[str, Payment]:
    """Create sample payments for testing."""
    payments = {
        'successful_payment': PaymentFactory.create(
            booking_id=sample_bookings['confirmed_booking'].id,
            amount=Decimal("350.00"),
            currency="USD",
            payment_method=PaymentMethod.CARD,
            payment_gateway="stripe",
            gateway_transaction_id="txn_successful_123",
            status=PaymentStatusEnum.COMPLETED
        ),
        'pending_payment': PaymentFactory.create(
            booking_id=sample_bookings['pending_booking'].id,
            amount=Decimal("85.00"),
            currency="USD",
            payment_method=PaymentMethod.CARD,
            payment_gateway="stripe",
            gateway_transaction_id="txn_pending_456",
            status=PaymentStatusEnum.PENDING
        ),
        'failed_payment': PaymentFactory.create(
            booking_id=sample_bookings['failed_payment_booking'].id,
            amount=Decimal("175.00"),
            currency="USD",
            payment_method=PaymentMethod.CARD,
            payment_gateway="stripe",
            gateway_transaction_id="txn_failed_789",
            status=PaymentStatusEnum.FAILED
        ),
        'refunded_payment': PaymentFactory.create(
            booking_id=sample_bookings['cancelled_booking'].id,
            amount=Decimal("260.00"),
            currency="USD",
            payment_method=PaymentMethod.CARD,
            payment_gateway="stripe",
            gateway_transaction_id="txn_refunded_101",
            status=PaymentStatusEnum.REFUNDED
        )
    }
    
    db_session.add_all(payments.values())
    await db_session.commit()
    
    for payment in payments.values():
        await db_session.refresh(payment)
    
    return payments


@pytest.fixture
async def sample_trip_locations(
    db_session: AsyncSession,
    sample_trips: Dict[str, Trip]
) -> Dict[str, List[TripLocation]]:
    """Create sample trip location data for testing."""
    base_time = datetime.utcnow()
    
    # Create location history for current trip
    current_trip_locations = [
        TripLocationFactory.create(
            trip_id=sample_trips['current_trip'].id,
            latitude=Decimal("40.7128"),  # New York
            longitude=Decimal("-74.0060"),
            speed=Decimal("0.0"),
            heading=Decimal("0.0"),
            recorded_at=base_time - timedelta(hours=2)
        ),
        TripLocationFactory.create(
            trip_id=sample_trips['current_trip'].id,
            latitude=Decimal("40.8000"),  # Moving north
            longitude=Decimal("-74.1000"),
            speed=Decimal("65.0"),
            heading=Decimal("315.0"),
            recorded_at=base_time - timedelta(hours=1, minutes=30)
        ),
        TripLocationFactory.create(
            trip_id=sample_trips['current_trip'].id,
            latitude=Decimal("41.0000"),  # Further north
            longitude=Decimal("-74.5000"),
            speed=Decimal("70.0"),
            heading=Decimal("320.0"),
            recorded_at=base_time - timedelta(hours=1)
        ),
        TripLocationFactory.create(
            trip_id=sample_trips['current_trip'].id,
            latitude=Decimal("41.2000"),  # Current position
            longitude=Decimal("-75.0000"),
            speed=Decimal("68.0"),
            heading=Decimal("315.0"),
            recorded_at=base_time - timedelta(minutes=15)
        )
    ]
    
    # Create location history for completed trip
    completed_trip_locations = [
        TripLocationFactory.create(
            trip_id=sample_trips['completed_trip'].id,
            latitude=Decimal("41.8781"),  # Chicago start
            longitude=Decimal("-87.6298"),
            speed=Decimal("0.0"),
            heading=Decimal("0.0"),
            recorded_at=base_time - timedelta(days=2)
        ),
        TripLocationFactory.create(
            trip_id=sample_trips['completed_trip'].id,
            latitude=Decimal("34.0522"),  # Los Angeles end
            longitude=Decimal("-118.2437"),
            speed=Decimal("0.0"),
            heading=Decimal("0.0"),
            recorded_at=base_time - timedelta(days=1)
        )
    ]
    
    all_locations = current_trip_locations + completed_trip_locations
    db_session.add_all(all_locations)
    await db_session.commit()
    
    for location in all_locations:
        await db_session.refresh(location)
    
    return {
        'current_trip': current_trip_locations,
        'completed_trip': completed_trip_locations
    }


@pytest.fixture
async def complete_test_scenario(
    db_session: AsyncSession,
    sample_users: Dict[str, User],
    sample_terminals: Dict[str, Terminal],
    sample_routes: Dict[str, Route],
    sample_buses: Dict[str, Bus],
    sample_trips: Dict[str, Trip],
    sample_bookings: Dict[str, Booking],
    sample_payments: Dict[str, Payment],
    sample_trip_locations: Dict[str, List[TripLocation]]
) -> Dict[str, Any]:
    """Create a complete test scenario with all related data."""
    return {
        'users': sample_users,
        'terminals': sample_terminals,
        'routes': sample_routes,
        'buses': sample_buses,
        'trips': sample_trips,
        'bookings': sample_bookings,
        'payments': sample_payments,
        'trip_locations': sample_trip_locations
    }


@pytest.fixture
def mock_external_services():
    """Mock external service responses."""
    return {
        'stripe': {
            'payment_intent_create': {
                'id': 'pi_test_123',
                'client_secret': 'pi_test_123_secret',
                'amount': 5000,
                'currency': 'usd',
                'status': 'requires_payment_method'
            },
            'payment_intent_confirm': {
                'id': 'pi_test_123',
                'status': 'succeeded',
                'amount': 5000,
                'currency': 'usd'
            }
        },
        'google_maps': {
            'geocode': {
                'results': [
                    {
                        'geometry': {
                            'location': {
                                'lat': 40.7128,
                                'lng': -74.0060
                            }
                        },
                        'formatted_address': '123 Broadway, New York, NY 10001, USA'
                    }
                ],
                'status': 'OK'
            },
            'directions': {
                'routes': [
                    {
                        'legs': [
                            {
                                'distance': {'value': 4500000, 'text': '4,500 km'},
                                'duration': {'value': 172800, 'text': '48 hours'}
                            }
                        ]
                    }
                ],
                'status': 'OK'
            }
        },
        'email_service': {
            'send_email': {
                'message_id': 'msg_test_123',
                'status': 'sent'
            }
        },
        'sms_service': {
            'send_sms': {
                'message_id': 'sms_test_456',
                'status': 'sent'
            }
        }
    }


@pytest.fixture
def api_test_data():
    """Common test data for API tests."""
    return {
        'valid_user_registration': {
            "email": "newuser@example.com",
            "password": "SecurePass123",
            "first_name": "New",
            "last_name": "User",
            "phone": "+1234567890"
        },
        'valid_user_login': {
            "email": "test@example.com",
            "password": "password123"
        },
        'valid_booking_request': {
            "trip_id": "trip-123",
            "seat_numbers": [1, 2]
        },
        'valid_payment_request': {
            "booking_id": "booking-123",
            "payment_method": "card"
        },
        'valid_location_update': {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "speed": 65.5,
            "heading": 180.0
        }
    }


@pytest.fixture
def performance_test_data():
    """Test data for performance testing."""
    return {
        'concurrent_users': 100,
        'requests_per_second': 50,
        'test_duration_seconds': 60,
        'acceptable_response_time_ms': 2000,
        'acceptable_error_rate_percent': 1.0
    }