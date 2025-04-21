from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


# Main Booking Model (For creating a booking)
class Booking(BaseModel):
    ticket_id: str  # The ride this booking is associated with
    code: str  # Unique code for the booking
    user_id: str  # User who made the booking
    pick_up_location: str  # Pick-up location of the ride
    drop_off_location: str  # Drop-off location for the ride
    fare_amount: float  # The amount charged for the fare
    isprotected: bool = False  # Whether the booking is protected (default: False)
    seats: List[dict]  # List of seat information (could be seat details in a dictionary)

    class Config:
        from_attributes = True  # Enable ORM mapping for SQLAlchemy models

# Schema for Booking Response
class BookingResponse(Booking):
    id: UUID  # Unique ID for the booking
    created_at: datetime  # The time the booking was created
    updated_at: datetime  # The time the booking was updated

    class Config:
        from_attributes = True  # Enable ORM mapping for SQLAlchemy models


# Schema for creating a new booking
class BookingCreate(Booking):
    code: Optional[str] = None

# Schema for updating an existing booking (BookingUpdate)
class BookingUpdate(BaseModel):
    ticket_id: UUID  # The ID of the ride for this booking
    code: Optional[str] = None  # Booking code (optional for update)
    pick_up_location: Optional[str] = None  # Pick-up location (optional for update)
    drop_off_location: Optional[str] = None  # Drop-off location (optional for update)
    fare_amount: Optional[float] = None  # Fare amount (optional for update)
    isprotected: Optional[bool] = None  # Whether the booking is protected (optional for update)
    seats: Optional[List[dict]] = None  # List of seats (optional for update)

    class Config:
        from_attributes = True  # Enable ORM mapping for SQLAlchemy models
