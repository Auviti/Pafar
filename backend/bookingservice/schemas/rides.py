from pydantic import BaseModel, root_validator, ValidationError,validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum
from typing import Union


# Enum for Ride Status
class RideStatus(str, Enum):
    UPCOMING = "UPCOMING"
    ASSIGNED = "ASSIGNED"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"

class RideClass(str, Enum):
    ECONOMY = "ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST_CLASS = "FIRST_CLASS"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"

class RideType(str, Enum):
    ROUND = "ROUND"
    ONE_WAY = "ONE_WAY"
    MULTICITY = "MULTICITY"

# Pydantic Schema for Ride
class Ride(BaseModel):
    name: Optional[str] = None
    status: RideStatus
    ride_class: RideClass
    ride_type: RideType
    vehicle_id: str
    trip_fare: float
    startlocation: str
    currentlocation:str
    endlocation: str
    starts_at: str
    ends_at: str
    suitcase: float = 0.0
    handluggage: float = 0.0
    otherluggage: float = 0.0

    class Config:
        from_attributes = True  # Enable ORM mapping for SQLAlchemy models

   
class RideCreate(Ride):
    pass  # Used when creating a new ride (no ride id)

class RideUpdate(Ride):
    
    pass
class RideFilter(BaseModel):
    id: Optional[UUID] = None
    name: Optional[str] = None
    status: Optional[RideStatus] = None
    ride_class: Optional[RideClass] = None
    ride_type: Optional[RideType] = None
    vehicle_id: Optional[str] = None
    trip_fare: Optional[float] = None
    startlocation: Optional[str] = None
    currentlocation:Optional[str] = None
    endlocation: Optional[str] = None
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    suitcase: Optional[float] = 0.0
    handluggage: Optional[float] = 0.0
    otherluggage: Optional[float] = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Enable ORM mapping for SQLAlchemy models

class RideResponse(Ride):
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
