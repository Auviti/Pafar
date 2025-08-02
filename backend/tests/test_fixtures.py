"""
Comprehensive test fixtures for the Pafar Transport Management Platform.
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient
from unittest.mock import Mock, AsyncMock

from app.main import app
from app.core.database import Base, get_db
from app.core.redis import get_redis
from app.core.config import settings
from backend.tests.factories import (
    UserFactory, TerminalFactory, RouteFactory, BusFactory, 
    TripFactory, BookingFactory, PaymentFactory, TripLocationFactory,
    TestDataBuilder, PerformanceTestDataBuilder, SecurityTestDataBuilder
)


# Test Database Configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    echo=False
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    class MockRedis:
        def __init__(self):
            self.data = {}
            self.expiry = {}
        
        async def get(self, key: str):
            if key in self.expiry:
                import time
                if time.time() > self.expiry[key]:
                    del self.data[key]
                    del self.expiry[key]
                    return None
            return self.data.get(key)
        
        async def setex(self, key: str, time: int, value):
            import time as time_module
            self.data[key] = value
            self.expiry[key] = time_module.time() + time
            return True
        
        async def set(self, key: str, value, ex=None):
            self.data[key] = value
            if ex:
                import time
                self.expiry[key] = time.time() + ex
            return True
        
        async def delete(self, key: str):
            if key in self.data:
                del self.data[key]
                if key in self.expiry:
                    del self.expiry[key]
                return True
            return False
        
        async def exists(self, key: str):
            return key in self.data
        
        async def expire(self, key: str, time: int):
            if key in self.data:
                import time as time_module
                self.expiry[key] = time_module.time() + time
                return True
            return False
        
        async def ttl(self, key: str):
            if key in self.expiry:
                import time
                remaining = self.expiry[key] - time.time()
                return max(0, int(remaining))
            return -1
        
        async def flushall(self):
            self.data.clear()
            self.expiry.clear()
            return True
        
        async def ping(self):
            return True
    
    return MockRedis()


@pytest.fixture
def override_get_db(db_session):
    """Override database dependency for testing."""
    async def _override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def override_get_redis(mock_redis):
    """Override Redis dependency for testing."""
    async def _override_get_redis():
        return mock_redis
    
    app.dependency_overrides[get_redis] = _override_get_redis
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(override_get_db, override_get_redis) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def authenticated_client(client, db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create authenticated test client."""
    # Create test user
    user_data = {
        "email": "test@example.com",
        "password": "password123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    # Register user
    await client.post("/api/v1/auth/register", json=user_data)
    
    # Login to get token
    login_response = await client.post("/api/v1/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    
    tokens = login_response.json()
    client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
    
    yield client


@pytest_asyncio.fixture
async def admin_client(client, db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create authenticated admin client."""
    # Create admin user
    admin_data = {
        "email": "admin@example.com",
        "password": "password123",
        "first_name": "Admin",
        "last_name": "User",
        "role": "admin"
    }
    
    # Register admin
    await client.post("/api/v1/auth/register", json=admin_data)
    
    # Login to get token
    login_response = await client.post("/api/v1/auth/login", json={
        "email": admin_data["email"],
        "password": admin_data["password"]
    })
    
    tokens = login_response.json()
    client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
    
    yield client


@pytest_asyncio.fixture
async def driver_client(client, db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create authenticated driver client."""
    # Create driver user
    driver_data = {
        "email": "driver@example.com",
        "password": "password123",
        "first_name": "Driver",
        "last_name": "User",
        "role": "driver"
    }
    
    # Register driver
    await client.post("/api/v1/auth/register", json=driver_data)
    
    # Login to get token
    login_response = await client.post("/api/v1/auth/login", json={
        "email": driver_data["email"],
        "password": driver_data["password"]
    })
    
    tokens = login_response.json()
    client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
    
    yield client


# Data Fixtures
@pytest.fixture
def sample_user():
    """Create sample user for testing."""
    return UserFactory.create()


@pytest.fixture
def sample_admin():
    """Create sample admin user for testing."""
    return UserFactory.create_admin()


@pytest.fixture
def sample_driver():
    """Create sample driver user for testing."""
    return UserFactory.create_driver()


@pytest.fixture
def sample_terminals():
    """Create sample terminals for testing."""
    origin, destination = TerminalFactory.create_pair()
    return {"origin": origin, "destination": destination}


@pytest.fixture
def sample_route(sample_terminals):
    """Create sample route for testing."""
    return RouteFactory.create(
        origin_terminal_id=sample_terminals["origin"].id,
        destination_terminal_id=sample_terminals["destination"].id
    )


@pytest.fixture
def sample_bus():
    """Create sample bus for testing."""
    return BusFactory.create()


@pytest.fixture
def sample_trip(sample_route, sample_bus, sample_driver):
    """Create sample trip for testing."""
    return TripFactory.create(
        route_id=sample_route.id,
        bus_id=sample_bus.id,
        driver_id=sample_driver.id
    )


@pytest.fixture
def sample_booking(sample_user, sample_trip):
    """Create sample booking for testing."""
    return BookingFactory.create(
        user_id=sample_user.id,
        trip_id=sample_trip.id
    )


@pytest.fixture
def sample_payment(sample_booking):
    """Create sample payment for testing."""
    return PaymentFactory.create(booking_id=sample_booking.id)


@pytest.fixture
def complete_booking_scenario():
    """Create complete booking scenario with all related objects."""
    return TestDataBuilder.create_complete_booking_scenario()


@pytest.fixture
def trip_with_tracking():
    """Create trip with location tracking data."""
    return TestDataBuilder.create_trip_with_tracking()


# Performance Test Fixtures
@pytest.fixture
def large_dataset():
    """Create large dataset for performance testing."""
    return PerformanceTestDataBuilder.create_large_dataset()


@pytest.fixture
def concurrent_booking_scenario():
    """Create scenario for testing concurrent bookings."""
    return PerformanceTestDataBuilder.create_concurrent_booking_scenario()


# Security Test Fixtures
@pytest.fixture
def injection_test_data():
    """Create data for injection testing."""
    return SecurityTestDataBuilder.create_injection_test_data()


@pytest.fixture
def authentication_bypass_scenarios():
    """Create scenarios for authentication bypass testing."""
    return SecurityTestDataBuilder.create_authentication_bypass_scenarios()


# Mock Service Fixtures
@pytest.fixture
def mock_stripe_client():
    """Mock Stripe client for payment testing."""
    mock_client = Mock()
    
    # Mock PaymentIntent
    mock_payment_intent = Mock()
    mock_payment_intent.id = "pi_test_123"
    mock_payment_intent.client_secret = "pi_test_123_secret"
    mock_payment_intent.status = "requires_payment_method"
    
    mock_client.PaymentIntent.create.return_value = mock_payment_intent
    mock_client.PaymentIntent.retrieve.return_value = mock_payment_intent
    mock_client.PaymentIntent.confirm.return_value = mock_payment_intent
    
    return mock_client


@pytest.fixture
def mock_google_maps_client():
    """Mock Google Maps client for location testing."""
    mock_client = Mock()
    
    # Mock geocoding
    mock_client.geocode.return_value = [
        {
            'geometry': {
                'location': {
                    'lat': 40.7128,
                    'lng': -74.0060
                }
            },
            'formatted_address': '123 Test St, New York, NY'
        }
    ]
    
    # Mock directions
    mock_client.directions.return_value = [
        {
            'legs': [
                {
                    'distance': {'value': 450000},  # meters
                    'duration': {'value': 18000}    # seconds
                }
            ]
        }
    ]
    
    return mock_client


@pytest.fixture
def mock_email_service():
    """Mock email service for notification testing."""
    mock_service = AsyncMock()
    mock_service.send_email.return_value = {"message_id": "msg_123"}
    return mock_service


@pytest.fixture
def mock_sms_service():
    """Mock SMS service for notification testing."""
    mock_service = AsyncMock()
    mock_service.send_sms.return_value = {"message_id": "sms_123"}
    return mock_service


@pytest.fixture
def mock_push_notification_service():
    """Mock push notification service for mobile testing."""
    mock_service = AsyncMock()
    mock_service.send_notification.return_value = {"message_id": "push_123"}
    return mock_service


# WebSocket Test Fixtures
@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket manager for real-time testing."""
    mock_manager = AsyncMock()
    mock_manager.connect.return_value = True
    mock_manager.disconnect.return_value = True
    mock_manager.broadcast_to_trip.return_value = True
    mock_manager.send_to_user.return_value = True
    return mock_manager


# Database State Fixtures
@pytest_asyncio.fixture
async def populated_db(db_session):
    """Create database with sample data."""
    # Create users
    passenger = UserFactory.create()
    driver = UserFactory.create_driver()
    admin = UserFactory.create_admin()
    
    # Create terminals
    origin, destination = TerminalFactory.create_pair()
    
    # Create route
    route = RouteFactory.create(
        origin_terminal_id=origin.id,
        destination_terminal_id=destination.id
    )
    
    # Create bus
    bus = BusFactory.create()
    
    # Create trip
    trip = TripFactory.create(
        route_id=route.id,
        bus_id=bus.id,
        driver_id=driver.id
    )
    
    # Create booking
    booking = BookingFactory.create(
        user_id=passenger.id,
        trip_id=trip.id
    )
    
    # Create payment
    payment = PaymentFactory.create(booking_id=booking.id)
    
    # Add all to session
    db_session.add_all([
        passenger, driver, admin,
        origin, destination, route,
        bus, trip, booking, payment
    ])
    await db_session.commit()
    
    return {
        'passenger': passenger,
        'driver': driver,
        'admin': admin,
        'origin': origin,
        'destination': destination,
        'route': route,
        'bus': bus,
        'trip': trip,
        'booking': booking,
        'payment': payment
    }


# Test Environment Fixtures
@pytest.fixture
def test_settings():
    """Override settings for testing."""
    original_settings = settings
    
    # Override with test values
    test_values = {
        'DATABASE_URL': TEST_DATABASE_URL,
        'REDIS_URL': 'redis://localhost:6379/15',  # Test Redis DB
        'SECRET_KEY': 'test-secret-key',
        'ACCESS_TOKEN_EXPIRE_MINUTES': 5,  # Short expiry for testing
        'STRIPE_SECRET_KEY': 'sk_test_123',
        'GOOGLE_MAPS_API_KEY': 'test_maps_key',
    }
    
    for key, value in test_values.items():
        setattr(settings, key, value)
    
    yield settings
    
    # Restore original settings
    for key in test_values.keys():
        setattr(settings, key, getattr(original_settings, key))


# Cleanup Fixtures
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Cleanup code here if needed


@pytest.fixture(scope="session", autouse=True)
def cleanup_after_session():
    """Cleanup after test session."""
    yield
    # Session cleanup code here if needed


# Parametrized Fixtures
@pytest.fixture(params=[
    {"role": "passenger", "factory": UserFactory.create},
    {"role": "driver", "factory": UserFactory.create_driver},
    {"role": "admin", "factory": UserFactory.create_admin},
])
def user_by_role(request):
    """Create user by role for parametrized testing."""
    return request.param["factory"]()


@pytest.fixture(params=[
    {"status": "pending", "payment_status": "pending"},
    {"status": "confirmed", "payment_status": "completed"},
    {"status": "cancelled", "payment_status": "refunded"},
])
def booking_by_status(request):
    """Create booking by status for parametrized testing."""
    return BookingFactory.create(
        status=request.param["status"],
        payment_status=request.param["payment_status"]
    )


# Error Simulation Fixtures
@pytest.fixture
def database_error_simulation():
    """Simulate database errors for testing."""
    def simulate_error(error_type="connection"):
        if error_type == "connection":
            return Exception("Database connection failed")
        elif error_type == "timeout":
            return Exception("Database query timeout")
        elif error_type == "constraint":
            return Exception("Database constraint violation")
        else:
            return Exception("Unknown database error")
    
    return simulate_error


@pytest.fixture
def network_error_simulation():
    """Simulate network errors for testing."""
    def simulate_error(error_type="timeout"):
        if error_type == "timeout":
            return Exception("Network timeout")
        elif error_type == "connection":
            return Exception("Connection refused")
        elif error_type == "dns":
            return Exception("DNS resolution failed")
        else:
            return Exception("Unknown network error")
    
    return simulate_error


# Performance Monitoring Fixtures
@pytest.fixture
def performance_monitor():
    """Monitor performance during tests."""
    import time
    import psutil
    import threading
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.memory_usage = []
            self.cpu_usage = []
            self.monitoring = False
            self.monitor_thread = None
        
        def start(self):
            self.start_time = time.time()
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor)
            self.monitor_thread.start()
        
        def stop(self):
            self.end_time = time.time()
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join()
        
        def _monitor(self):
            while self.monitoring:
                self.memory_usage.append(psutil.virtual_memory().percent)
                self.cpu_usage.append(psutil.cpu_percent())
                time.sleep(0.1)
        
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
        
        @property
        def avg_memory_usage(self):
            return sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0
        
        @property
        def avg_cpu_usage(self):
            return sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0
    
    return PerformanceMonitor()


# Test Data Validation Fixtures
@pytest.fixture
def data_validator():
    """Validate test data integrity."""
    class DataValidator:
        @staticmethod
        def validate_user(user):
            assert user.email is not None
            assert "@" in user.email
            assert user.first_name is not None
            assert user.last_name is not None
            assert user.role in ["passenger", "driver", "admin"]
        
        @staticmethod
        def validate_booking(booking):
            assert booking.user_id is not None
            assert booking.trip_id is not None
            assert booking.seat_numbers is not None
            assert len(booking.seat_numbers) > 0
            assert booking.total_amount > 0
            assert booking.booking_reference is not None
        
        @staticmethod
        def validate_payment(payment):
            assert payment.booking_id is not None
            assert payment.amount > 0
            assert payment.currency is not None
            assert payment.payment_method is not None
        
        @staticmethod
        def validate_trip(trip):
            assert trip.route_id is not None
            assert trip.bus_id is not None
            assert trip.driver_id is not None
            assert trip.departure_time is not None
            assert trip.fare > 0
            assert trip.available_seats >= 0
    
    return DataValidator()


# Export all fixtures for easy import
__all__ = [
    'event_loop', 'db_session', 'mock_redis', 'override_get_db', 'override_get_redis',
    'client', 'authenticated_client', 'admin_client', 'driver_client',
    'sample_user', 'sample_admin', 'sample_driver', 'sample_terminals', 'sample_route',
    'sample_bus', 'sample_trip', 'sample_booking', 'sample_payment',
    'complete_booking_scenario', 'trip_with_tracking', 'large_dataset',
    'concurrent_booking_scenario', 'injection_test_data', 'authentication_bypass_scenarios',
    'mock_stripe_client', 'mock_google_maps_client', 'mock_email_service',
    'mock_sms_service', 'mock_push_notification_service', 'mock_websocket_manager',
    'populated_db', 'test_settings', 'cleanup_after_test', 'cleanup_after_session',
    'user_by_role', 'booking_by_status', 'database_error_simulation',
    'network_error_simulation', 'performance_monitor', 'data_validator'
]