from pydantic import BaseModel, root_validator, ValidationError,validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum
from typing import Union


# Enum for Ride Status
class RideStatus(str, Enum):
    ASSIGNED = "Assigned"
    ONGOING = "Ongoing"
    COMPLETED = "Completed"
    CANCELED = "Canceled"

class Location(BaseModel):
    latitude: Union[float, int]
    longitude: Union[float, int]
    address: str

    # Custom validator for location fields to ensure data integrity
    @validator('latitude', 'longitude')
    def check_coordinates(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError(f"{v} must be a number.")
        return v

    @validator('address')
    def check_address(cls, v):
        if not isinstance(v, str):
            raise ValueError(f"Address must be a string.")
        return v

# Pydantic Schema for Ride
class Ride(BaseModel):
    name: Optional[str] = None
    status: RideStatus
    vehicle_id: str
    trip_fare: float
    startlocation: dict
    currentlocation: dict
    endlocation: dict
    starts_at: datetime
    ends_at: datetime
    suitcase: float = 0.0
    handluggage: float = 0.0
    otherluggage: float = 0.0

    class Config:
        from_attributes = True  # Enable ORM mapping for SQLAlchemy models

    # Validator to ensure that location contains latitude, longitude, and address
    # Root validator to validate multiple fields at once
    @root_validator(pre=True)
    def check_location_fields(cls, values):
        startlocation = values.get('startlocation')
        endlocation = values.get('endlocation')

        # Ensure both startlocation and endlocation are provided
        if startlocation:
            # Ensure the location contains latitude, longitude, and address for startlocation
            required_fields = ['latitude', 'longitude', 'address']
            for field_name in required_fields:
                if field_name not in startlocation:
                    raise ValueError(f"Startlocation must include {', '.join(required_fields)}.")
                if not isinstance(startlocation['latitude'], (int, float)):
                    raise ValueError("Latitude must be a number.")
                if not isinstance(startlocation['longitude'], (int, float)):
                    raise ValueError("Longitude must be a number.")
                if not isinstance(startlocation['address'], str):
                    raise ValueError("Address must be a string.")
        
        if endlocation:
            # Ensure the location contains latitude, longitude, and address for endlocation
            required_fields = ['latitude', 'longitude', 'address']
            for field_name in required_fields:
                if field_name not in endlocation:
                    raise ValueError(f"Endlocation must include {', '.join(required_fields)}.")
                if not isinstance(endlocation['latitude'], (int, float)):
                    raise ValueError("Latitude must be a number.")
                if not isinstance(endlocation['longitude'], (int, float)):
                    raise ValueError("Longitude must be a number.")
                if not isinstance(endlocation['address'], str):
                    raise ValueError("Address must be a string.")
        
        return values

class RideCreate(Ride):
    pass  # Used when creating a new ride (no ride id)

class RideUpdate(Ride):
    
    pass

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
