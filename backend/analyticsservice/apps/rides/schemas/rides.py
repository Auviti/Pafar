from pydantic import BaseModel, validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

# Enum for Ride Status
class RideStatus(str, Enum):
    ASSIGNED = "Assigned"
    ONGOING = "Ongoing"
    COMPLETED = "Completed"
    CANCELED = "Canceled"

# Pydantic Schema for Ride
class RideBase(BaseModel):
    name: Optional[str] = None
    status: RideStatus
    driver_id: UUID
    bus_id:UUID
    trip_fare: float
    startlocation: Optional[dict] = None
    currentlocation: Optional[dict] = None
    endlocation: Optional[dict] = None
    starts_at: datetime
    ends_at: Optional[datetime] = None
    suitcase: float = 0.0
    handluggage: float = 0.0
    otherluggage: float = 0.0

    class Config:
        from_attributes = True  # Enable ORM mapping for SQLAlchemy models

    # Validator to ensure that location contains latitude, longitude, and address
    @validator('startlocation', 'endlocation', pre=True, always=True)
    def check_location_fields(cls, v, field):
        if v:
            # Ensure the location contains latitude, longitude, and address
            required_fields = ['latitude', 'longitude', 'address']
            for field_name in required_fields:
                if field_name not in v:
                    raise ValueError(f"Location must include {', '.join(required_fields)}.")

            # Check if latitude and longitude are numbers
            if not isinstance(v['latitude'], (int, float)):
                raise ValueError(f"{field_name.capitalize()} must be a number.")
            if not isinstance(v['longitude'], (int, float)):
                raise ValueError(f"{field_name.capitalize()} must be a number.")

            # Ensure address is a string
            if not isinstance(v['address'], str):
                raise ValueError("Address must be a string.")
        return v

class RideCreate(RideBase):
    pass  # Used when creating a new ride (no ride id)

class RideUpdate(RideBase):
    
    status: Optional[RideStatus] = None
    bus_id: Optional[UUID] = None
    trip_fare: Optional[float] = None
    startlocation: Optional[dict] = None
    currentlocation: Optional[dict] = None
    endlocation: Optional[dict] = None
    suitcase: Optional[float] = None
    handluggage: Optional[float] = None
    otherluggage: Optional[float] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None

class Ride(RideBase):
    id: UUID  # This will be returned when fetching the ride from the database
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mapping for SQLAlchemy models

    @property
    def duration(self):
        """Calculate duration of the ride (end - start)"""
        if self.starts_at and self.ends_at:
            return (self.ends_at - self.starts_at).total_seconds()  # Duration in seconds
        return None

    @property
    def total_fare(self):
        """Calculate the total fare, considering luggage prices"""
        luggage_fare = 0.02 * (self.suitcase + self.handluggage + self.otherluggage)
        return self.trip_fare + luggage_fare
