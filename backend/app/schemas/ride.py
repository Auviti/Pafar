"""
Ride Pydantic schemas for request/response validation.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator
from ..models.ride import RideStatus


class LocationBase(BaseModel):
    """Base location schema."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: str = Field(..., min_length=5, max_length=500)
    city: str = Field(..., min_length=2, max_length=100)
    country: str = Field(..., min_length=2, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)


class LocationCreate(LocationBase):
    """Schema for location creation."""
    pass


class LocationResponse(LocationBase):
    """Schema for location response."""
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class RideBase(BaseModel):
    """Base ride schema."""
    estimated_fare: Decimal = Field(..., gt=0, decimal_places=2)
    estimated_duration: int = Field(..., gt=0)  # minutes
    distance: float = Field(..., gt=0)  # kilometers


class RideCreate(RideBase):
    """Schema for ride creation."""
    pickup_location: LocationCreate
    destination_location: LocationCreate
    
    @validator('estimated_fare')
    def validate_fare(cls, v):
        """Validate fare is reasonable."""
        if v > 10000:  # $10,000 max fare
            raise ValueError('Fare cannot exceed $10,000')
        return v
    
    @validator('distance')
    def validate_distance(cls, v):
        """Validate distance is reasonable."""
        if v > 1000:  # 1000km max distance
            raise ValueError('Distance cannot exceed 1000 kilometers')
        return v


class RideUpdate(BaseModel):
    """Schema for ride updates."""
    status: Optional[RideStatus] = None
    actual_fare: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    actual_duration: Optional[int] = Field(None, gt=0)
    cancellation_reason: Optional[str] = Field(None, max_length=500)


class RideResponse(RideBase):
    """Schema for ride response."""
    id: UUID
    customer_id: UUID
    driver_id: Optional[UUID] = None
    pickup_location: LocationResponse
    destination_location: LocationResponse
    status: RideStatus
    actual_fare: Optional[Decimal] = None
    actual_duration: Optional[int] = None
    requested_at: datetime
    accepted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    
    class Config:
        from_attributes = True


class DriverLocationUpdate(BaseModel):
    """Schema for driver location updates."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    heading: Optional[float] = Field(None, ge=0, lt=360)
    speed: Optional[float] = Field(None, ge=0)  # km/h
    is_available: bool = True


class DriverLocationResponse(BaseModel):
    """Schema for driver location response."""
    id: UUID
    driver_id: UUID
    latitude: float
    longitude: float
    heading: Optional[float] = None
    speed: Optional[float] = None
    is_available: bool
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RideSearchFilters(BaseModel):
    """Schema for ride search filters."""
    status: Optional[RideStatus] = None
    customer_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)