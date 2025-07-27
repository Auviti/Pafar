"""
Pydantic schemas for review and rating operations.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator


class ReviewBase(BaseModel):
    """Base review schema."""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = Field(None, max_length=1000, description="Optional review comment")


class ReviewCreate(ReviewBase):
    """Schema for creating a new review."""
    booking_id: UUID = Field(..., description="ID of the booking being reviewed")


class ReviewUpdate(BaseModel):
    """Schema for updating a review."""
    rating: Optional[int] = Field(None, ge=1, le=5, description="Updated rating from 1 to 5")
    comment: Optional[str] = Field(None, max_length=1000, description="Updated review comment")


class ReviewResponse(ReviewBase):
    """Schema for review response."""
    id: UUID
    booking_id: UUID
    user_id: UUID
    driver_id: UUID
    is_moderated: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReviewWithDetails(ReviewResponse):
    """Schema for review with user and booking details."""
    user_name: str
    driver_name: str
    trip_route: str
    trip_date: datetime
    
    class Config:
        from_attributes = True


class ReviewModerationUpdate(BaseModel):
    """Schema for admin review moderation."""
    is_moderated: bool = Field(..., description="Moderation status")
    action_reason: Optional[str] = Field(None, max_length=500, description="Reason for moderation action")


class ReviewStats(BaseModel):
    """Schema for review statistics."""
    total_reviews: int
    average_rating: float
    rating_distribution: dict[int, int]  # rating -> count


class DriverRatingStats(ReviewStats):
    """Schema for driver rating statistics."""
    driver_id: UUID
    driver_name: str


class BusRatingStats(ReviewStats):
    """Schema for bus rating statistics."""
    bus_id: UUID
    bus_license_plate: str


class ReviewListResponse(BaseModel):
    """Schema for paginated review list."""
    reviews: list[ReviewWithDetails]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool