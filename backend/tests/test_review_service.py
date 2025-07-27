"""
Unit tests for review service.
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


@pytest_asyncio.fixture
async def review_service(db_session: AsyncSession):
    """Create review service instance."""
    return ReviewService(db_session)


@pytest_asyncio.fixture
async def sample_user(db_session: AsyncSession):
    """Create a sample passenger user."""
    user = User(
        id=uuid4(),
        email="passenger@test.com",
        phone="+1234567890",
        password_hash="hashed_password",
        first_name="John",
        last_name="Doe",
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
    """Create a sample driver user."""
    driver = User(
        id=uuid4(),
        email="driver@test.com",
        phone="+1234567891",
        password_hash="hashed_password",
        first_name="Jane",
        last_name="Smith",
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
        id=uuid4(),
        email="admin@test.com",
        phone="+1234567892",
        password_hash="hashed_password",
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        is_verified=True,
        is_active=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def sample_terminals(db_session: AsyncSession):
    """Create sample terminals."""
    origin = Terminal(
        id=uuid4(),
        name="Origin Terminal",
        city="Origin City",
        address="123 Origin St",
        latitude=Decimal("40.7128"),
        longitude=Decimal("-74.0060"),
        is_active=True
    )
    
    destination = Terminal(
        id=uuid4(),
        name="Destination Terminal",
        city="Destination City",
        address="456 Destination Ave",
        latitude=Decimal("34.0522"),
        longitude=Decimal("-118.2437"),
        is_active=True
    )
    
    db_session.add_all([origin, destination])
    await db_session.commit()
    await db_session.refresh(origin)
    await db_session.refresh(destination)
    return origin, destination


@pytest_asyncio.fixture
async def sample_route(db_session: AsyncSession, sample_terminals):
    """Create a sample route."""
    origin, destination = sample_terminals
    route = Route(
        id=uuid4(),
        origin_terminal_id=origin.id,
        destination_terminal_id=destination.id,
        distance_km=Decimal("500.0"),
        estimated_duration_minutes=480,
        base_fare=Decimal("50.00"),
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
        id=uuid4(),
        license_plate="ABC-123",
        model="Mercedes Sprinter",
        capacity=50,
        amenities={"wifi": True, "ac": True},
        is_active=True
    )
    db_session.add(bus)
    await db_session.commit()
    await db_session.refresh(bus)
    return bus


@pytest_asyncio.fixture
async def sample_trip(db_session: AsyncSession, sample_route, sample_bus, sample_driver):
    """Create a sample trip."""
    trip = Trip(
        id=uuid4(),
        route_id=sample_route.id,
        bus_id=sample_bus.id,
        driver_id=sample_driver.id,
        departure_time=datetime.utcnow() + timedelta(hours=2),
        arrival_time=None,
        status=TripStatus.COMPLETED,
        fare=Decimal("50.00"),
        available_seats=48
    )
    db_session.add(trip)
    await db_session.commit()
    await db_session.refresh(trip)
    return trip


@pytest_asyncio.fixture
async def sample_booking(db_session: AsyncSession, sample_user, sample_trip):
    """Create a sample completed booking."""
    booking = Booking(
        id=uuid4(),
        user_id=sample_user.id,
        trip_id=sample_trip.id,
        seat_numbers=[1, 2],
        total_amount=Decimal("100.00"),
        status=BookingStatus.COMPLETED,
        booking_reference="BK123456",
        payment_status=PaymentStatus.COMPLETED
    )
    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)
    return booking


class TestReviewService:
    """Test cases for ReviewService."""
    
    @pytest.mark.asyncio
    async def test_create_review_success(
        self, 
        review_service: ReviewService, 
        sample_user: User, 
        sample_booking: Booking
    ):
        """Test successful review creation."""
        review_data = ReviewCreate(
            booking_id=sample_booking.id,
            rating=5,
            comment="Excellent service!"
        )
        
        result = await review_service.create_review(sample_user.id, review_data)
        
        assert result.booking_id == sample_booking.id
        assert result.user_id == sample_user.id
        assert result.rating == 5
        assert result.comment == "Excellent service!"
        assert result.is_moderated == False
    
    @pytest.mark.asyncio
    async def test_create_review_booking_not_found(
        self, 
        review_service: ReviewService, 
        sample_user: User
    ):
        """Test review creation with non-existent booking."""
        review_data = ReviewCreate(
            booking_id=uuid4(),
            rating=5,
            comment="Great trip!"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await review_service.create_review(sample_user.id, review_data)
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()
    
    async def test_create_review_duplicate(
        self, 
        review_service: ReviewService, 
        sample_user: User, 
        sample_booking: Booking,
        db_session: AsyncSession
    ):
        """Test creating duplicate review for same booking."""
        # Create first review
        review_data = ReviewCreate(
            booking_id=sample_booking.id,
            rating=5,
            comment="First review"
        )
        await review_service.create_review(sample_user.id, review_data)
        
        # Try to create second review
        review_data2 = ReviewCreate(
            booking_id=sample_booking.id,
            rating=4,
            comment="Second review"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await review_service.create_review(sample_user.id, review_data2)
        
        assert exc_info.value.status_code == 409
        assert "already exists" in exc_info.value.detail.lower()
    
    async def test_update_review_success(
        self, 
        review_service: ReviewService, 
        sample_user: User, 
        sample_booking: Booking
    ):
        """Test successful review update."""
        # Create review first
        review_data = ReviewCreate(
            booking_id=sample_booking.id,
            rating=4,
            comment="Good service"
        )
        review = await review_service.create_review(sample_user.id, review_data)
        
        # Update review
        update_data = ReviewUpdate(
            rating=5,
            comment="Excellent service after update!"
        )
        
        result = await review_service.update_review(sample_user.id, review.id, update_data)
        
        assert result.rating == 5
        assert result.comment == "Excellent service after update!"
        assert result.is_moderated == False  # Should reset moderation status
    
    async def test_update_review_not_found(
        self, 
        review_service: ReviewService, 
        sample_user: User
    ):
        """Test updating non-existent review."""
        update_data = ReviewUpdate(rating=5)
        
        with pytest.raises(HTTPException) as exc_info:
            await review_service.update_review(sample_user.id, uuid4(), update_data)
        
        assert exc_info.value.status_code == 404
    
    async def test_get_review_success(
        self, 
        review_service: ReviewService, 
        sample_user: User, 
        sample_booking: Booking
    ):
        """Test getting a review by ID."""
        # Create review first
        review_data = ReviewCreate(
            booking_id=sample_booking.id,
            rating=5,
            comment="Great trip!"
        )
        review = await review_service.create_review(sample_user.id, review_data)
        
        # Get review
        result = await review_service.get_review(review.id)
        
        assert result is not None
        assert result.id == review.id
        assert result.rating == 5
        assert result.user_name == sample_user.full_name
    
    async def test_get_review_not_found(self, review_service: ReviewService):
        """Test getting non-existent review."""
        result = await review_service.get_review(uuid4())
        assert result is None
    
    async def test_get_reviews_for_driver(
        self, 
        review_service: ReviewService, 
        sample_user: User, 
        sample_driver: User,
        sample_booking: Booking,
        db_session: AsyncSession
    ):
        """Test getting reviews for a specific driver."""
        # Create and moderate a review
        review_data = ReviewCreate(
            booking_id=sample_booking.id,
            rating=5,
            comment="Great driver!"
        )
        review = await review_service.create_review(sample_user.id, review_data)
        
        # Moderate the review
        db_review = await db_session.get(Review, review.id)
        db_review.is_moderated = True
        await db_session.commit()
        
        # Get reviews for driver
        result = await review_service.get_reviews_for_driver(sample_driver.id)
        
        assert result.total == 1
        assert len(result.reviews) == 1
        assert result.reviews[0].driver_id == sample_driver.id
    
    async def test_get_driver_rating_stats(
        self, 
        review_service: ReviewService, 
        sample_user: User, 
        sample_driver: User,
        sample_booking: Booking,
        db_session: AsyncSession
    ):
        """Test getting driver rating statistics."""
        # Create and moderate a review
        review_data = ReviewCreate(
            booking_id=sample_booking.id,
            rating=5,
            comment="Excellent driver!"
        )
        review = await review_service.create_review(sample_user.id, review_data)
        
        # Moderate the review
        db_review = await db_session.get(Review, review.id)
        db_review.is_moderated = True
        await db_session.commit()
        
        # Get stats
        result = await review_service.get_driver_rating_stats(sample_driver.id)
        
        assert result.driver_id == sample_driver.id
        assert result.driver_name == sample_driver.full_name
        assert result.total_reviews == 1
        assert result.average_rating == 5.0
        assert result.rating_distribution[5] == 1
    
    async def test_get_bus_rating_stats(
        self, 
        review_service: ReviewService, 
        sample_user: User, 
        sample_bus: Bus,
        sample_booking: Booking,
        db_session: AsyncSession
    ):
        """Test getting bus rating statistics."""
        # Create and moderate a review
        review_data = ReviewCreate(
            booking_id=sample_booking.id,
            rating=4,
            comment="Good bus!"
        )
        review = await review_service.create_review(sample_user.id, review_data)
        
        # Moderate the review
        db_review = await db_session.get(Review, review.id)
        db_review.is_moderated = True
        await db_session.commit()
        
        # Get stats
        result = await review_service.get_bus_rating_stats(sample_bus.id)
        
        assert result.bus_id == sample_bus.id
        assert result.bus_license_plate == sample_bus.license_plate
        assert result.total_reviews == 1
        assert result.average_rating == 4.0
        assert result.rating_distribution[4] == 1
    
    async def test_moderate_review(
        self, 
        review_service: ReviewService, 
        sample_user: User, 
        sample_booking: Booking
    ):
        """Test review moderation."""
        # Create review
        review_data = ReviewCreate(
            booking_id=sample_booking.id,
            rating=5,
            comment="Great service!"
        )
        review = await review_service.create_review(sample_user.id, review_data)
        
        # Moderate review
        moderation_data = ReviewModerationUpdate(
            is_moderated=True,
            action_reason="Approved after review"
        )
        
        result = await review_service.moderate_review(review.id, moderation_data)
        
        assert result.is_moderated == True
    
    async def test_delete_review_success(
        self, 
        review_service: ReviewService, 
        sample_user: User, 
        sample_booking: Booking
    ):
        """Test successful review deletion."""
        # Create review
        review_data = ReviewCreate(
            booking_id=sample_booking.id,
            rating=5,
            comment="Great service!"
        )
        review = await review_service.create_review(sample_user.id, review_data)
        
        # Delete review
        result = await review_service.delete_review(sample_user.id, review.id)
        
        assert result == True
        
        # Verify review is deleted
        deleted_review = await review_service.get_review(review.id)
        assert deleted_review is None
    
    async def test_delete_review_not_found(
        self, 
        review_service: ReviewService, 
        sample_user: User
    ):
        """Test deleting non-existent review."""
        with pytest.raises(HTTPException) as exc_info:
            await review_service.delete_review(sample_user.id, uuid4())
        
        assert exc_info.value.status_code == 404
    
    async def test_get_unmoderated_reviews(
        self, 
        review_service: ReviewService, 
        sample_user: User, 
        sample_booking: Booking
    ):
        """Test getting unmoderated reviews."""
        # Create unmoderated review
        review_data = ReviewCreate(
            booking_id=sample_booking.id,
            rating=5,
            comment="Needs moderation"
        )
        await review_service.create_review(sample_user.id, review_data)
        
        # Get unmoderated reviews
        result = await review_service.get_unmoderated_reviews()
        
        assert result.total == 1
        assert len(result.reviews) == 1
        assert result.reviews[0].is_moderated == False