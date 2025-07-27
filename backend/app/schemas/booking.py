"""
Pydantic schemas for booking operations.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator
from app.models.booking import BookingStatus, PaymentStatus


class SeatReservationRequest(BaseModel):
    """Schema for temporary seat reservation."""
    trip_id: UUID
    seat_numbers: List[int] = Field(..., min_items=1, max_items=4)
    
    @validator('seat_numbers')
    def validate_seat_numbers(cls, v):
        if not all(seat > 0 for seat in v):
            raise ValueError('Seat numbers must be positive integers')
        if len(set(v)) != len(v):
            raise ValueError('Duplicate seat numbers not allowed')
        return sorted(v)


class BookingCreate(BaseModel):
    """Schema for creating a new booking."""
    trip_id: UUID
    seat_numbers: List[int] = Field(..., min_items=1, max_items=4)
    
    @validator('seat_numbers')
    def validate_seat_numbers(cls, v):
        if not all(seat > 0 for seat in v):
            raise ValueError('Seat numbers must be positive integers')
        if len(set(v)) != len(v):
            raise ValueError('Duplicate seat numbers not allowed')
        return sorted(v)


class BookingUpdate(BaseModel):
    """Schema for updating booking status."""
    status: Optional[BookingStatus] = None
    payment_status: Optional[PaymentStatus] = None


class TripSearchRequest(BaseModel):
    """Schema for trip search with filters."""
    origin_terminal_id: Optional[UUID] = None
    destination_terminal_id: Optional[UUID] = None
    departure_date: Optional[datetime] = None
    min_seats: Optional[int] = Field(None, ge=1, le=4)
    max_fare: Optional[Decimal] = Field(None, gt=0)


class TerminalInfo(BaseModel):
    """Schema for terminal information."""
    id: UUID
    name: str
    city: str
    address: Optional[str] = None
    
    model_config = {"from_attributes": True}


class RouteInfo(BaseModel):
    """Schema for route information."""
    id: UUID
    origin_terminal: TerminalInfo
    destination_terminal: TerminalInfo
    distance_km: Optional[Decimal] = None
    estimated_duration_minutes: Optional[int] = None
    base_fare: Decimal
    
    model_config = {"from_attributes": True}


class BusInfo(BaseModel):
    """Schema for bus information."""
    id: UUID
    license_plate: str
    model: Optional[str] = None
    capacity: int
    amenities: Optional[dict] = None
    
    model_config = {"from_attributes": True}


class TripDetails(BaseModel):
    """Schema for detailed trip information."""
    id: UUID
    route: RouteInfo
    bus: BusInfo
    departure_time: datetime
    arrival_time: Optional[datetime] = None
    status: str
    fare: Decimal
    available_seats: Optional[int] = None
    
    model_config = {"from_attributes": True}


class BookingResponse(BaseModel):
    """Schema for booking response."""
    id: UUID
    booking_reference: str
    trip: TripDetails
    seat_numbers: List[int]
    total_amount: Decimal
    status: BookingStatus
    payment_status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class SeatAvailabilityResponse(BaseModel):
    """Schema for seat availability response."""
    trip_id: UUID
    total_seats: int
    available_seats: List[int]
    occupied_seats: List[int]
    temporarily_reserved_seats: List[int]


class BookingCancellationRequest(BaseModel):
    """Schema for booking cancellation."""
    reason: Optional[str] = Field(None, max_length=500)


class BookingListResponse(BaseModel):
    """Schema for booking list response."""
    bookings: List[BookingResponse]
    total: int
    page: int
    size: int