"""
Review service for handling ratings and feedback operations.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from app.models.tracking import Review
from app.models.booking import Booking, BookingStatus
from app.models.user import User
from app.models.fleet import Trip, Bus, Route
from app.schemas.review import (
    ReviewCreate, ReviewUpdate, ReviewResponse, ReviewWithDetails,
    ReviewModerationUpdate, ReviewStats, DriverRatingStats, BusRatingStats,
    ReviewListResponse
)
from app.core.database import get_db
from fastapi import HTTPException, status, Depends


class ReviewService:
    """Service for managing reviews and ratings."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_review(self, user_id: UUID, review_data: ReviewCreate) -> ReviewResponse:
        """Create a new review for a completed booking."""
        # Verify booking exists and belongs to user
        booking_query = select(Booking).options(
            selectinload(Booking.trip).selectinload(Trip.driver)
        ).where(
            and_(
                Booking.id == review_data.booking_id,
                Booking.user_id == user_id,
                Booking.status == BookingStatus.COMPLETED
            )
        )
        
        result = await self.db.execute(booking_query)
        booking = result.scalar_one_or_none()
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found or not eligible for review"
            )
        
        # Check if review already exists
        existing_review_query = select(Review).where(
            and_(
                Review.booking_id == review_data.booking_id,
                Review.user_id == user_id
            )
        )
        
        result = await self.db.execute(existing_review_query)
        existing_review = result.scalar_one_or_none()
        
        if existing_review:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Review already exists for this booking"
            )
        
        # Create new review
        review = Review(
            booking_id=review_data.booking_id,
            user_id=user_id,
            driver_id=booking.trip.driver_id,
            rating=review_data.rating,
            comment=review_data.comment,
            is_moderated=False
        )
        
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        
        return ReviewResponse.from_orm(review)
    
    async def update_review(self, user_id: UUID, review_id: UUID, review_data: ReviewUpdate) -> ReviewResponse:
        """Update an existing review."""
        # Get review and verify ownership
        review_query = select(Review).where(
            and_(
                Review.id == review_id,
                Review.user_id == user_id
            )
        )
        
        result = await self.db.execute(review_query)
        review = result.scalar_one_or_none()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        # Update fields
        if review_data.rating is not None:
            review.rating = review_data.rating
        if review_data.comment is not None:
            review.comment = review_data.comment
        
        # Reset moderation status if content changed
        review.is_moderated = False
        
        await self.db.commit()
        await self.db.refresh(review)
        
        return ReviewResponse.from_orm(review)
    
    async def get_review(self, review_id: UUID) -> Optional[ReviewWithDetails]:
        """Get a single review with details."""
        query = select(Review).options(
            selectinload(Review.user),
            selectinload(Review.driver),
            selectinload(Review.booking).selectinload(Booking.trip).selectinload(Trip.route).selectinload(Route.origin_terminal),
            selectinload(Review.booking).selectinload(Booking.trip).selectinload(Trip.route).selectinload(Route.destination_terminal)
        ).where(Review.id == review_id)
        
        result = await self.db.execute(query)
        review = result.scalar_one_or_none()
        
        if not review:
            return None
        
        return self._build_review_with_details(review)
    
    async def get_reviews_for_driver(
        self, 
        driver_id: UUID, 
        page: int = 1, 
        per_page: int = 10,
        moderated_only: bool = True
    ) -> ReviewListResponse:
        """Get reviews for a specific driver."""
        offset = (page - 1) * per_page
        
        # Build query conditions
        conditions = [Review.driver_id == driver_id]
        if moderated_only:
            conditions.append(Review.is_moderated == True)
        
        # Get reviews with details
        query = select(Review).options(
            selectinload(Review.user),
            selectinload(Review.driver),
            selectinload(Review.booking).selectinload(Booking.trip).selectinload(Trip.route).selectinload(Route.origin_terminal),
            selectinload(Review.booking).selectinload(Booking.trip).selectinload(Trip.route).selectinload(Route.destination_terminal)
        ).where(and_(*conditions)).order_by(desc(Review.created_at)).offset(offset).limit(per_page)
        
        result = await self.db.execute(query)
        reviews = result.scalars().all()
        
        # Get total count
        count_query = select(func.count(Review.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Build response
        review_details = [self._build_review_with_details(review) for review in reviews]
        
        return ReviewListResponse(
            reviews=review_details,
            total=total,
            page=page,
            per_page=per_page,
            has_next=offset + per_page < total,
            has_prev=page > 1
        )
    
    async def get_reviews_for_booking(self, booking_id: UUID) -> List[ReviewWithDetails]:
        """Get reviews for a specific booking."""
        query = select(Review).options(
            selectinload(Review.user),
            selectinload(Review.driver),
            selectinload(Review.booking).selectinload(Booking.trip).selectinload(Trip.route).selectinload(Route.origin_terminal),
            selectinload(Review.booking).selectinload(Booking.trip).selectinload(Trip.route).selectinload(Route.destination_terminal)
        ).where(Review.booking_id == booking_id)
        
        result = await self.db.execute(query)
        reviews = result.scalars().all()
        
        return [self._build_review_with_details(review) for review in reviews]
    
    async def get_unmoderated_reviews(
        self, 
        page: int = 1, 
        per_page: int = 20
    ) -> ReviewListResponse:
        """Get unmoderated reviews for admin review."""
        offset = (page - 1) * per_page
        
        query = select(Review).options(
            selectinload(Review.user),
            selectinload(Review.driver),
            selectinload(Review.booking).selectinload(Booking.trip).selectinload(Trip.route).selectinload(Route.origin_terminal),
            selectinload(Review.booking).selectinload(Booking.trip).selectinload(Trip.route).selectinload(Route.destination_terminal)
        ).where(Review.is_moderated == False).order_by(Review.created_at).offset(offset).limit(per_page)
        
        result = await self.db.execute(query)
        reviews = result.scalars().all()
        
        # Get total count
        count_query = select(func.count(Review.id)).where(Review.is_moderated == False)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Build response
        review_details = [self._build_review_with_details(review) for review in reviews]
        
        return ReviewListResponse(
            reviews=review_details,
            total=total,
            page=page,
            per_page=per_page,
            has_next=offset + per_page < total,
            has_prev=page > 1
        )
    
    async def moderate_review(
        self, 
        review_id: UUID, 
        moderation_data: ReviewModerationUpdate
    ) -> ReviewResponse:
        """Moderate a review (admin only)."""
        review_query = select(Review).where(Review.id == review_id)
        result = await self.db.execute(review_query)
        review = result.scalar_one_or_none()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        review.is_moderated = moderation_data.is_moderated
        
        await self.db.commit()
        await self.db.refresh(review)
        
        return ReviewResponse.from_orm(review)
    
    async def delete_review(self, user_id: UUID, review_id: UUID) -> bool:
        """Delete a review (user can delete their own review)."""
        review_query = select(Review).where(
            and_(
                Review.id == review_id,
                Review.user_id == user_id
            )
        )
        
        result = await self.db.execute(review_query)
        review = result.scalar_one_or_none()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        await self.db.delete(review)
        await self.db.commit()
        
        return True
    
    async def get_driver_rating_stats(self, driver_id: UUID) -> DriverRatingStats:
        """Get rating statistics for a driver."""
        # Get driver info
        driver_query = select(User).where(User.id == driver_id)
        driver_result = await self.db.execute(driver_query)
        driver = driver_result.scalar_one_or_none()
        
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver not found"
            )
        
        # Get review statistics
        stats_query = select(
            func.count(Review.id).label('total_reviews'),
            func.avg(Review.rating).label('average_rating'),
            Review.rating
        ).where(
            and_(
                Review.driver_id == driver_id,
                Review.is_moderated == True
            )
        ).group_by(Review.rating)
        
        result = await self.db.execute(stats_query)
        stats_data = result.all()
        
        # Build rating distribution
        rating_distribution = {i: 0 for i in range(1, 6)}
        total_reviews = 0
        total_rating_sum = 0
        
        for row in stats_data:
            rating_distribution[row.rating] = row.total_reviews
            total_reviews += row.total_reviews
            total_rating_sum += row.rating * row.total_reviews
        
        average_rating = total_rating_sum / total_reviews if total_reviews > 0 else 0.0
        
        return DriverRatingStats(
            driver_id=driver_id,
            driver_name=driver.full_name,
            total_reviews=total_reviews,
            average_rating=round(average_rating, 2),
            rating_distribution=rating_distribution
        )
    
    async def get_bus_rating_stats(self, bus_id: UUID) -> BusRatingStats:
        """Get rating statistics for a bus."""
        # Get bus info
        bus_query = select(Bus).where(Bus.id == bus_id)
        bus_result = await self.db.execute(bus_query)
        bus = bus_result.scalar_one_or_none()
        
        if not bus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bus not found"
            )
        
        # Get review statistics through trips
        stats_query = select(
            func.count(Review.id).label('total_reviews'),
            func.avg(Review.rating).label('average_rating'),
            Review.rating
        ).select_from(
            Review.__table__.join(Booking.__table__).join(Trip.__table__)
        ).where(
            and_(
                Trip.bus_id == bus_id,
                Review.is_moderated == True
            )
        ).group_by(Review.rating)
        
        result = await self.db.execute(stats_query)
        stats_data = result.all()
        
        # Build rating distribution
        rating_distribution = {i: 0 for i in range(1, 6)}
        total_reviews = 0
        total_rating_sum = 0
        
        for row in stats_data:
            rating_distribution[row.rating] = row.total_reviews
            total_reviews += row.total_reviews
            total_rating_sum += row.rating * row.total_reviews
        
        average_rating = total_rating_sum / total_reviews if total_reviews > 0 else 0.0
        
        return BusRatingStats(
            bus_id=bus_id,
            bus_license_plate=bus.license_plate,
            total_reviews=total_reviews,
            average_rating=round(average_rating, 2),
            rating_distribution=rating_distribution
        )
    
    def _build_review_with_details(self, review: Review) -> ReviewWithDetails:
        """Build a review with details from the review object."""
        # Build trip route string
        trip_route = "Unknown Route"
        if (review.booking and review.booking.trip and review.booking.trip.route and 
            review.booking.trip.route.origin_terminal and review.booking.trip.route.destination_terminal):
            trip_route = f"{review.booking.trip.route.origin_terminal.name} → {review.booking.trip.route.destination_terminal.name}"
        
        return ReviewWithDetails(
            id=review.id,
            booking_id=review.booking_id,
            user_id=review.user_id,
            driver_id=review.driver_id,
            rating=review.rating,
            comment=review.comment,
            is_moderated=review.is_moderated,
            created_at=review.created_at,
            user_name=review.user.full_name if review.user else "Unknown User",
            driver_name=review.driver.full_name if review.driver else "Unknown Driver",
            trip_route=trip_route,
            trip_date=review.booking.trip.departure_time if (review.booking and review.booking.trip) else review.created_at
        )


async def get_review_service(db: AsyncSession = Depends(get_db)) -> ReviewService:
    """Dependency to get review service."""
    return ReviewService(db)