"""
Review API endpoints for ratings and feedback management.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin_user
from app.models.user import User
from app.services.review_service import ReviewService, get_review_service
from app.schemas.review import (
    ReviewCreate, ReviewUpdate, ReviewResponse, ReviewWithDetails,
    ReviewModerationUpdate, DriverRatingStats, BusRatingStats,
    ReviewListResponse
)

router = APIRouter()


@router.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service)
):
    """
    Create a new review for a completed booking.
    
    - **booking_id**: ID of the completed booking to review
    - **rating**: Rating from 1 to 5 stars
    - **comment**: Optional review comment
    """
    return await review_service.create_review(current_user.id, review_data)


@router.get("/reviews/{review_id}", response_model=ReviewWithDetails)
async def get_review(
    review_id: UUID,
    review_service: ReviewService = Depends(get_review_service)
):
    """Get a specific review by ID with details."""
    review = await review_service.get_review(review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    return review


@router.put("/reviews/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: UUID,
    review_data: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service)
):
    """
    Update an existing review.
    
    Users can only update their own reviews.
    """
    return await review_service.update_review(current_user.id, review_id, review_data)


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: UUID,
    current_user: User = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service)
):
    """
    Delete a review.
    
    Users can only delete their own reviews.
    """
    await review_service.delete_review(current_user.id, review_id)


@router.get("/drivers/{driver_id}/reviews", response_model=ReviewListResponse)
async def get_driver_reviews(
    driver_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=50, description="Items per page"),
    moderated_only: bool = Query(True, description="Show only moderated reviews"),
    review_service: ReviewService = Depends(get_review_service)
):
    """
    Get reviews for a specific driver.
    
    - **driver_id**: ID of the driver
    - **page**: Page number for pagination
    - **per_page**: Number of reviews per page
    - **moderated_only**: Whether to show only moderated reviews
    """
    return await review_service.get_reviews_for_driver(
        driver_id, page, per_page, moderated_only
    )


@router.get("/bookings/{booking_id}/reviews", response_model=List[ReviewWithDetails])
async def get_booking_reviews(
    booking_id: UUID,
    review_service: ReviewService = Depends(get_review_service)
):
    """Get all reviews for a specific booking."""
    return await review_service.get_reviews_for_booking(booking_id)


@router.get("/drivers/{driver_id}/rating-stats", response_model=DriverRatingStats)
async def get_driver_rating_stats(
    driver_id: UUID,
    review_service: ReviewService = Depends(get_review_service)
):
    """
    Get rating statistics for a driver.
    
    Returns total reviews, average rating, and rating distribution.
    """
    return await review_service.get_driver_rating_stats(driver_id)


@router.get("/buses/{bus_id}/rating-stats", response_model=BusRatingStats)
async def get_bus_rating_stats(
    bus_id: UUID,
    review_service: ReviewService = Depends(get_review_service)
):
    """
    Get rating statistics for a bus.
    
    Returns total reviews, average rating, and rating distribution.
    """
    return await review_service.get_bus_rating_stats(bus_id)


# Admin endpoints
@router.get("/admin/reviews/unmoderated", response_model=ReviewListResponse)
async def get_unmoderated_reviews(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_admin: User = Depends(get_current_admin_user),
    review_service: ReviewService = Depends(get_review_service)
):
    """
    Get unmoderated reviews for admin review.
    
    Admin only endpoint.
    """
    return await review_service.get_unmoderated_reviews(page, per_page)


@router.put("/admin/reviews/{review_id}/moderate", response_model=ReviewResponse)
async def moderate_review(
    review_id: UUID,
    moderation_data: ReviewModerationUpdate,
    current_admin: User = Depends(get_current_admin_user),
    review_service: ReviewService = Depends(get_review_service)
):
    """
    Moderate a review (approve or reject).
    
    Admin only endpoint.
    """
    return await review_service.moderate_review(review_id, moderation_data)