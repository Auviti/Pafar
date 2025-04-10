from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


# Enum for Booking Status
class BookingStatus(str, Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    IN_PROGRESS = "In Progress"


# Main Booking Model (For creating a booking)
class Booking(BaseModel):
    ride_id: UUID  # The ride this booking is associated with
    code: str  # Unique code for the booking
    barcode: str  # Barcode associated with the booking
    user_id: str  # User who made the booking
    pick_up_location: str  # Pick-up location of the ride
    drop_off_location: str  # Drop-off location for the ride
    booking_time: Optional[datetime] = None  # Time of booking (can be optional for creation)
    booking_status: BookingStatus = BookingStatus.PENDING  # Default status is 'Pending'
    fare_amount: float  # The amount charged for the fare
    isprotected: bool = False  # Whether the booking is protected (default: False)
    seats: List[dict]  # List of seat information (could be seat details in a dictionary)

    class Config:
        from_attributes = True  # Enable ORM mapping for SQLAlchemy models

# Schema for Booking Response
class BookingResponse(Booking):
    id: UUID  # Unique ID for the booking
    booking_time: datetime  # The time the booking was created
    booking_status: BookingStatus  # Status of the booking (Pending, Completed, etc.)

    class Config:
        from_attributes = True  # Enable ORM mapping for SQLAlchemy models


# Schema for creating a new booking
class BookingCreate(Booking):
    ride_id: UUID  # The ID of the ride for this booking
    code: str  # Unique code for the booking
    barcode: str  # Barcode for the booking
    user_id: UUID  # The user ID who made the booking
    pick_up_location: str  # The location for pick-up
    drop_off_location: str  # The location for drop-off
    fare_amount: float  # The fare amount for the trip
    isprotected: bool = False  # Whether the booking is protected (default: False)
    seats: List[dict]  # List of seats in the booking (could be seat details in a dictionary)

    class Config:
        from_attributes = True  # Enable ORM mapping for SQLAlchemy models

# Schema for updating an existing booking (BookingUpdate)
class BookingUpdate(BaseModel):
    ride_id: UUID  # The ID of the ride for this booking
    code: Optional[str] = None  # Booking code (optional for update)
    barcode: Optional[str] = None  # Booking barcode (optional for update)
    pick_up_location: Optional[str] = None  # Pick-up location (optional for update)
    drop_off_location: Optional[str] = None  # Drop-off location (optional for update)
    booking_status: Optional[BookingStatus] = None  # Booking status (optional for update)
    fare_amount: Optional[float] = None  # Fare amount (optional for update)
    isprotected: Optional[bool] = None  # Whether the booking is protected (optional for update)
    seats: Optional[List[dict]] = None  # List of seats (optional for update)

    class Config:
        from_attributes = True  # Enable ORM mapping for SQLAlchemy models
