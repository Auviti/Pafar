"""
Simple unit tests for review service.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.services.review_service import ReviewService
from app.models.user import User, UserRole
from app.models.fleet import Terminal, Route, Bus, Trip, TripStatus
from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.tracking import Review
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewModerationUpdate


@pytest.mark.asyncio
async def test_create_review_service(db_session: AsyncSession):
    """Test creating review service instance."""
    service = ReviewService(db_session)
    assert service is not None
    assert service.db == db_session


@pytest.mark.asyncio
async def test_create_review_success(db_session: AsyncSession):
    """Test successful review creation."""
    # Create test data
    user = User(
        id=uuid4(),
        email="test@example.com",
        phone="+1234567890",
        password_hash="hashed",
        first_name="Test",
        last_name="User",
        role=UserRole.PASSENGER,
        is_verified=True,
        is_active=True
    )
    
    driver = User(
        id=uuid4(),
        email="driver@example.com",
        phone="+1234567891",
        password_hash="hashed",
        first_name="Test",
        last_name="Driver",
        role=UserRole.DRIVER,
        is_verified=True,
        is_active=True
    )
    
    origin = Terminal(
        id=uuid4(),
        name="Origin Terminal",
        city="Origin City",
        is_active=True
    )
    
    destination = Terminal(
        id=uuid4(),
        name="Destination Terminal", 
        city="Destination City",
        is_active=True
    )
    
    route = Route(
        id=uuid4(),
        origin_terminal_id=origin.id,
        destination_terminal_id=destination.id,
        base_fare=Decimal("50.00"),
        is_active=True
    )
    
    bus = Bus(
        id=uuid4(),
        license_plate="ABC-123",
        capacity=50,
        is_active=True
    )
    
    trip = Trip(
        id=uuid4(),
        route_id=route.id,
        bus_id=bus.id,
        driver_id=driver.id,
        departure_time=datetime.utcnow() + timedelta(hours=2),
        status=TripStatus.COMPLETED,
        fare=Decimal("50.00"),
        available_seats=48
    )
    
    booking = Booking(
        id=uuid4(),
        user_id=user.id,
        trip_id=trip.id,
        seat_numbers=[1, 2],
        total_amount=Decimal("100.00"),
        status=BookingStatus.COMPLETED,
        booking_reference="BK123456",
        payment_status=PaymentStatus.COMPLETED
    )
    
    # Add all to database
    db_session.add_all([user, driver, origin, destination, route, bus, trip, booking])
    await db_session.commit()
    
    # Test review creation
    service = ReviewService(db_session)
    review_data = ReviewCreate(
        booking_id=booking.id,
        rating=5,
        comment="Excellent service!"
    )
    
    result = await service.create_review(user.id, review_data)
    
    assert result.booking_id == booking.id
    assert result.user_id == user.id
    assert result.rating == 5
    assert result.comment == "Excellent service!"
    assert result.is_moderated == False


@pytest.mark.asyncio
async def test_create_review_booking_not_found(db_session: AsyncSession):
    """Test review creation with non-existent booking."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        phone="+1234567890",
        password_hash="hashed",
        first_name="Test",
        last_name="User",
        role=UserRole.PASSENGER,
        is_verified=True,
        is_active=True
    )
    
    db_session.add(user)
    await db_session.commit()
    
    service = ReviewService(db_session)
    review_data = ReviewCreate(
        booking_id=uuid4(),
        rating=5,
        comment="Great trip!"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await service.create_review(user.id, review_data)
    
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_get_review_not_found(db_session: AsyncSession):
    """Test getting non-existent review."""
    service = ReviewService(db_session)
    result = await service.get_review(uuid4())
    assert result is None