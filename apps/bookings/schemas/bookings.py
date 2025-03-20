from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

# Booking Create Schema
class BookingCreate(BaseModel):
    user_id: uuid.UUID  # The ID of the user making the booking
    driver_id: uuid.UUID  # The ID of the assigned driver
    pick_up_location: str  # Pick-up location
    drop_off_location: str  # Drop-off location
    booking_time: Optional[datetime] = None  # Optional, defaults to current time
    fare_amount: float  # Fare for the trip

    class Config:
        orm_mode = True


# Booking Read Schema (used for responses)
class BookingRead(BookingCreate):
    id: uuid.UUID  # The ID of the booking
    booking_status: str  # The status of the booking (Pending, Completed, etc.)
    booking_time: datetime  # The time when the booking was made

    class Config:
        orm_mode = True
