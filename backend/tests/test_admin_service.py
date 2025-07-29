"""
Unit tests for admin service functionality.
"""
import pytest
import pytest_asyncio
import json
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.admin_service import AdminService
from app.models.user import User, UserRole
from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.fleet import Trip, TripStatus, Bus, Route, Terminal
from app.models.payment import Payment
from app.models.tracking import Review, TripLocation
from app.schemas.admin import (
    UserSearchFilters, UserManagementAction, FleetAssignment,
    ReviewModerationAction, FraudAlert
)
from app.core.redis import redis_client


@pytest_asyncio.fixture
async def admin_service(db_session: AsyncSession):
    """Create admin service instance."""
    return AdminService(db_session)


@pytest_asyncio.fixture
async def sample_user(db_session: AsyncSession):
    """Create a sample user."""
    user = User(
        email="test@example.com",
        phone="+1234567890",
        password_hash="hashed_password",
        first_name="Test",
        last_name="User",
        role=UserRole.PASSENGER,
        is_verified=True,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_driver(db_session: AsyncSession):
    """Create a sample driver."""
    driver = User(
        email="driver@example.com",
        phone="+1234567891",
        password_hash="hashed_password",
        first_name="Test",
        last_name="Driver",
        role=UserRole.DRIVER,
        is_verified=True,
        is_active=True
    )
    db_session.add(driver)
    await db_session.commit()
    await db_session.refresh(driver)
    return driver


@pytest_asyncio.fixture
async def sample_admin(db_session: AsyncSession):
    """Create a sample admin user."""
    admin = User(
        email="admin@example.com",
        phone="+1234567892",
        password_hash="hashed_password",
        first_name="Test",
        last_name="Admin",
        role=UserRole.ADMIN,
        is_verified=True,
        is_active=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def sample_bus(db_session: AsyncSession):
    """Create a sample bus."""
    bus = Bus(
        license_plate="ABC123",
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
async def sample_route(db_session: AsyncSession):
    """Create a sample route with terminals."""
    # Create terminals
    origin = Terminal(
        name="Origin Terminal",
        city="Origin City",
        address="123 Origin St",
        latitude=40.7128,
        longitude=-74.0060,
        is_active=True
    )
    destination = Terminal(
        name="Destination Terminal",
        city="Destination City",
        address="456 Destination Ave",
        latitude=40.7589,
        longitude=-73.9851,
        is_active=True
    )
    
    db_session.add(origin)
    db_session.add(destination)
    await db_session.commit()
    await db_session.refresh(origin)
    await db_session.refresh(destination)
    
    # Create route
    route = Route(
        origin_terminal_id=origin.id,
        destination_terminal_id=destination.id,
        distance_km=50.0,
        estimated_duration_minutes=120,
        base_fare=25.00,
        is_active=True
    )
    db_session.add(route)
    await db_session.commit()
    await db_session.refresh(route)
    return route


@pytest_asyncio.fixture
async def sample_booking(db_session: AsyncSession, sample_user, sample_driver, sample_bus, sample_route):
    """Create a sample booking with trip."""
    # Create trip
    trip = Trip(
        route_id=sample_route.id,
        bus_id=sample_bus.id,
        driver_id=sample_driver.id,
        departure_time=datetime.utcnow() + timedelta(hours=2),
        fare=25.00,
        available_seats=19,
        status=TripStatus.SCHEDULED
    )
    db_session.add(trip)
    await db_session.commit()
    await db_session.refresh(trip)
    
    # Create booking
    booking = Booking(
        user_id=sample_user.id,
        trip_id=trip.id,
        seat_numbers=[1],
        total_amount=25.00,
        status=BookingStatus.CONFIRMED,
        payment_status=PaymentStatus.COMPLETED,
        booking_reference="BK123456"
    )
    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)
    return booking


@pytest_asyncio.fixture
async def sample_review(db_session: AsyncSession, sample_booking, sample_user, sample_driver):
    """Create a sample review."""
    review = Review(
        booking_id=sample_booking.id,
        user_id=sample_user.id,
        driver_id=sample_driver.id,
        rating=4,
        comment="Great trip!",
        is_moderated=False
    )
    db_session.add(review)
    await db_session.commit()
    await db_session.refresh(review)
    return review


@pytest.mark.asyncio
class TestAdminService:
    """Test cases for AdminService."""
    
    async def test_get_dashboard_metrics(self, admin_service, sample_user, sample_booking):
        """Test getting dashboard metrics."""
        # Create some test data
        payment = Payment(
            booking_id=sample_booking.id,
            amount=25.00,
            currency="USD",
            payment_method="card",
            payment_gateway="stripe",
            status="completed"
        )
        admin_service.db.add(payment)
        await admin_service.db.commit()
        
        # Mock Redis for fraud alerts
        with patch.object(redis_client, 'get', return_value=None):
            metrics = await admin_service.get_dashboard_metrics()
        
        assert metrics.total_users >= 1
        assert metrics.active_users >= 1
        assert metrics.total_bookings >= 1
        assert metrics.total_revenue >= 25.00
        assert isinstance(metrics.fraud_alerts, int)
    
    async def test_search_users_with_filters(self, admin_service, sample_user):
        """Test user search with various filters."""
        filters = UserSearchFilters(
            email="test",
            role=UserRole.PASSENGER,
            is_active=True
        )
        
        result = await admin_service.search_users(filters, page=1, page_size=10)
        
        assert result.total_count >= 1
        assert len(result.users) >= 1
        assert result.page == 1
        assert result.page_size == 10
        assert any(user.email == sample_user.email for user in result.users)
    
    async def test_search_users_no_results(self, admin_service):
        """Test user search with no matching results."""
        filters = UserSearchFilters(email="nonexistent@example.com")
        
        result = await admin_service.search_users(filters, page=1, page_size=10)
        
        assert result.total_count == 0
        assert len(result.users) == 0
    
    async def test_manage_user_suspend(self, admin_service, sample_user, sample_admin):
        """Test suspending a user."""
        action = UserManagementAction(
            action="suspend",
            reason="Violation of terms"
        )
        
        with patch.object(redis_client, 'setex'):
            result = await admin_service.manage_user(sample_user.id, action, sample_admin.id)
        
        assert result["success"] is True
        assert "suspended" in result["message"]
        
        # Verify user is suspended
        await admin_service.db.refresh(sample_user)
        assert sample_user.is_active is False
    
    async def test_manage_user_activate(self, admin_service, sample_user, sample_admin):
        """Test activating a user."""
        # First suspend the user
        sample_user.is_active = False
        await admin_service.db.commit()
        
        action = UserManagementAction(
            action="activate",
            reason="Appeal approved"
        )
        
        with patch.object(redis_client, 'setex'):
            result = await admin_service.manage_user(sample_user.id, action, sample_admin.id)
        
        assert result["success"] is True
        assert "activated" in result["message"]
        
        # Verify user is activated
        await admin_service.db.refresh(sample_user)
        assert sample_user.is_active is True
    
    async def test_manage_user_verify(self, admin_service, sample_user, sample_admin):
        """Test verifying a user."""
        # Make user unverified
        sample_user.is_verified = False
        await admin_service.db.commit()
        
        action = UserManagementAction(
            action="verify",
            reason="Manual verification"
        )
        
        with patch.object(redis_client, 'setex'):
            result = await admin_service.manage_user(sample_user.id, action, sample_admin.id)
        
        assert result["success"] is True
        assert "verified" in result["message"]
        
        # Verify user is verified
        await admin_service.db.refresh(sample_user)
        assert sample_user.is_verified is True
    
    async def test_manage_user_reset_password(self, admin_service, sample_user, sample_admin):
        """Test resetting user password."""
        action = UserManagementAction(
            action="reset_password",
            reason="User requested reset"
        )
        
        with patch.object(redis_client, 'setex'), patch.object(redis_client, 'delete'):
            result = await admin_service.manage_user(sample_user.id, action, sample_admin.id)
        
        assert result["success"] is True
        assert "Password reset" in result["message"]
        assert "Temporary password:" in result["message"]
    
    async def test_manage_user_not_found(self, admin_service, sample_admin):
        """Test managing non-existent user."""
        action = UserManagementAction(action="suspend")
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await admin_service.manage_user(uuid4(), action, sample_admin.id)
    
    async def test_assign_fleet_success(self, admin_service, sample_bus, sample_driver, sample_route, sample_admin):
        """Test successful fleet assignment."""
        assignment = FleetAssignment(
            bus_id=sample_bus.id,
            driver_id=sample_driver.id,
            route_id=sample_route.id,
            departure_time=datetime.utcnow() + timedelta(hours=2),
            fare=30.00
        )
        
        with patch.object(redis_client, 'setex'):
            result = await admin_service.assign_fleet(assignment, sample_admin.id)
        
        assert result["success"] is True
        assert "assigned successfully" in result["message"]
        assert "trip_id" in result
    
    async def test_assign_fleet_bus_not_found(self, admin_service, sample_driver, sample_route, sample_admin):
        """Test fleet assignment with non-existent bus."""
        assignment = FleetAssignment(
            bus_id=uuid4(),
            driver_id=sample_driver.id,
            route_id=sample_route.id,
            departure_time=datetime.utcnow() + timedelta(hours=2),
            fare=30.00
        )
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await admin_service.assign_fleet(assignment, sample_admin.id)
    
    async def test_assign_fleet_driver_not_found(self, admin_service, sample_bus, sample_route, sample_admin):
        """Test fleet assignment with non-existent driver."""
        assignment = FleetAssignment(
            bus_id=sample_bus.id,
            driver_id=uuid4(),
            route_id=sample_route.id,
            departure_time=datetime.utcnow() + timedelta(hours=2),
            fare=30.00
        )
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await admin_service.assign_fleet(assignment, sample_admin.id)
    
    async def test_get_live_trip_data(self, admin_service, sample_booking):
        """Test getting live trip data."""
        # Refresh booking to load trip relationship
        await admin_service.db.refresh(sample_booking, ['trip'])
        
        # Update trip status to in transit
        trip = sample_booking.trip
        trip.status = TripStatus.IN_TRANSIT
        await admin_service.db.commit()
        
        # Add location data
        location = TripLocation(
            trip_id=trip.id,
            latitude=40.7128,
            longitude=-74.0060,
            speed=60.0,
            heading=90.0
        )
        admin_service.db.add(location)
        await admin_service.db.commit()
        
        live_data = await admin_service.get_live_trip_data()
        
        assert len(live_data) >= 1
        trip_data = live_data[0]
        assert trip_data.trip_id == trip.id
        assert trip_data.status == TripStatus.IN_TRANSIT
        assert trip_data.current_location is not None
        assert trip_data.passenger_count >= 1
    
    async def test_moderate_review_approve(self, admin_service, sample_review, sample_admin):
        """Test approving a review."""
        action = ReviewModerationAction(
            action="approve",
            reason="Content is appropriate"
        )
        
        with patch.object(redis_client, 'setex'):
            result = await admin_service.moderate_review(sample_review.id, action, sample_admin.id)
        
        assert result["success"] is True
        assert "approved" in result["message"]
        
        # Verify review is moderated
        await admin_service.db.refresh(sample_review)
        assert sample_review.is_moderated is True
    
    async def test_moderate_review_flag(self, admin_service, sample_review, sample_admin):
        """Test flagging a review."""
        action = ReviewModerationAction(
            action="flag",
            reason="Inappropriate language",
            admin_notes="Contains profanity"
        )
        
        with patch.object(redis_client, 'get', return_value=None), \
             patch.object(redis_client, 'set'), \
             patch.object(redis_client, 'setex'):
            result = await admin_service.moderate_review(sample_review.id, action, sample_admin.id)
        
        assert result["success"] is True
        assert "flagged" in result["message"]
    
    async def test_create_fraud_alert(self, admin_service, sample_user):
        """Test creating a fraud alert."""
        with patch.object(redis_client, 'get', return_value=None), \
             patch.object(redis_client, 'set'):
            alert = await admin_service.create_fraud_alert(
                alert_type="suspicious_activity",
                severity="high",
                description="Multiple failed login attempts",
                user_id=sample_user.id
            )
        
        assert alert.alert_type == "suspicious_activity"
        assert alert.severity == "high"
        assert alert.user_id == sample_user.id
        assert alert.status == "open"
    
    async def test_get_fraud_alerts(self, admin_service):
        """Test getting fraud alerts."""
        # Mock Redis data
        mock_alerts = [
            {
                "id": str(uuid4()),
                "alert_type": "test_alert",
                "severity": "medium",
                "description": "Test alert",
                "metadata": {},
                "status": "open",
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        with patch.object(redis_client, 'get', return_value=json.dumps(mock_alerts)):
            result = await admin_service.get_fraud_alerts(page=1, page_size=10)
        
        assert result.total_count == 1
        assert len(result.alerts) == 1
        assert result.alerts[0].alert_type == "test_alert"
    
    async def test_trigger_fraud_detection(self, admin_service, sample_user, sample_booking):
        """Test triggering fraud detection."""
        with patch.object(redis_client, 'get', return_value=None), \
             patch.object(redis_client, 'set'), \
             patch.object(redis_client, 'setex'):
            # This should not raise an exception
            await admin_service.trigger_fraud_detection(sample_user.id, sample_booking.id)
    
    async def test_rapid_booking_fraud_detection(self, admin_service, sample_user):
        """Test rapid booking fraud detection."""
        # Create multiple recent bookings
        for i in range(6):  # More than the threshold of 5
            booking = Booking(
                user_id=sample_user.id,
                trip_id=uuid4(),  # Mock trip ID
                seat_numbers=[i+1],
                total_amount=25.00,
                status=BookingStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
                booking_reference=f"BK{i:06d}",
                created_at=datetime.utcnow() - timedelta(minutes=5)
            )
            admin_service.db.add(booking)
        
        await admin_service.db.commit()
        
        with patch.object(redis_client, 'get', return_value=None), \
             patch.object(redis_client, 'set'), \
             patch.object(redis_client, 'setex'):
            await admin_service._check_rapid_booking_fraud(sample_user.id)
    
    async def test_get_system_health(self, admin_service):
        """Test getting system health metrics."""
        # Mock the redis client's redis attribute to have a ping method
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        
        with patch.object(redis_client, 'redis', mock_redis):
            health = await admin_service.get_system_health()
        
        assert health.database_status in ["healthy", "unhealthy"]
        assert health.redis_status in ["healthy", "unhealthy"]
        assert isinstance(health.api_response_time, float)
        assert isinstance(health.active_connections, int)
        assert isinstance(health.memory_usage, float)
        assert isinstance(health.cpu_usage, float)
        assert isinstance(health.disk_usage, float)
    
    async def test_get_unmoderated_reviews(self, admin_service, sample_review):
        """Test getting unmoderated reviews."""
        result = await admin_service.get_unmoderated_reviews(page=1, page_size=10)
        
        assert result["total_count"] >= 1
        assert len(result["reviews"]) >= 1
        assert result["page"] == 1
        assert result["page_size"] == 10
        
        # Check review format
        review = result["reviews"][0]
        assert "id" in review
        assert "user_name" in review
        assert "driver_name" in review
        assert "rating" in review
        assert "comment" in review
    
    async def test_get_flagged_reviews(self, admin_service, sample_review):
        """Test getting flagged reviews."""
        # Mock flagged reviews in Redis
        mock_flagged = [
            {
                "review_id": str(sample_review.id),
                "reason": "Inappropriate content",
                "flagged_at": datetime.utcnow().isoformat(),
                "status": "pending_investigation"
            }
        ]
        
        with patch.object(redis_client, 'get', return_value=json.dumps(mock_flagged)):
            result = await admin_service.get_flagged_reviews()
        
        assert result["total_count"] >= 1
        assert len(result["flagged_reviews"]) >= 1
        
        # Check flagged review format
        flagged_review = result["flagged_reviews"][0]
        assert "id" in flagged_review
        assert "flagged_reason" in flagged_review
        assert "flagged_at" in flagged_review