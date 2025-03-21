from pydantic import BaseModel
from datetime import datetime
import uuid
from enum import Enum

# Enum for Ride Status
class RideStatusEnum(str, Enum):
    ASSIGNED = "Assigned"
    ONGOING = "Ongoing"
    COMPLETED = "Completed"
    CANCELED = "Canceled"

# Ride Status Create Schema
class RideCreate(BaseModel):
    booking_id: uuid.UUID  # The ID of the booking
    ride_status: RideStatusEnum  # The status of the ride (Assigned, Ongoing, etc.)
    location: Optional[Dict[str, float]] = None  # Location data, optional

    # Validator to ensure that location contains latitude, longitude, and address
    @validator('location')
    def check_location_fields(cls, v):
        if v:
            if 'latitude' not in v or 'longitude' not in v or 'address' not in v:
                raise ValueError("Location must include latitude, longitude, and address.")
            if not isinstance(v['latitude'], (int, float)):
                raise ValueError("Latitude must be a number.")
            if not isinstance(v['longitude'], (int, float)):
                raise ValueError("Longitude must be a number.")
            if not isinstance(v['address'], str):
                raise ValueError("Address must be a string.")
        return v

    class Config:
        from_attributes = True


# Ride Status Read Schema (used for responses)
class RideRead(RideStatusCreate):
    id: uuid.UUID  # The ID of the ride status
    status_update_time: datetime  # The time when the status was updated

    class Config:
        from_attributes = True
