from sqlalchemy import Integer, String, ForeignKey, Enum, DateTime, JSON, Float, CheckConstraint
from sqlalchemy.orm import relationship
from core.database import Base, CHAR_LENGTH
from sqlalchemy.orm import mapped_column
from datetime import datetime
from enum import Enum 
import uuid
from sqlalchemy.dialects.postgresql import UUID
import sys

# Database type detection
if 'postgresql' in sys.argv:
    # Use native UUID for PostgreSQL
    UUIDType = UUID(as_uuid=True)
    mappeditem = UUID
    default = uuid.uuid4  # Changed from uuid4 to uuid.uuid4 (correct)
else:
    # Use string representation for other databases
    UUIDType = String(36)
    mappeditem = str
    default = lambda: str(uuid.uuid4())

class Location(BaseModel):
    latitude: float
    longitude: float
    address: str
# Enum for Ride Status
class RideStatus(Enum):
    UPCOMING = "UpComing"
    ASSIGNED = "Assigned"
    ONGOING = "Ongoing"
    COMPLETED = "Completed"
    CANCELED = "Canceled"

class RideClass(Enum):
    ECONOMY = "economy"
    BUSINESS = "business"
    FIRST_CLASS = "first_class"
    PREMIUM_ECONOMY = "premium_economy"

# Ride Modelx
class Ride(Base):
    __tablename__ = "ride"

    # Ride ID (UUID as the primary key)
    id: mapped_column[UUID] = mapped_column(UUIDType, primary_key=True, default=default)
    name: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)
    # Ride Status (Assigned, Ongoing, Completed, Canceled)
    status: mapped_column[RideStatus] = mapped_column(Enum(RideStatus), nullable=False)
    ride_class: mapped_column[RideClass] = mapped_column(Enum(RideClass), default=RideClass.ECONOMY)  # Class of the trip (Economy, Business, etc.)
    
    # Foreign key referencing the Driver table (UUID)
    bus_id: mapped_column[UUID] = mapped_column(ForeignKey("bus.id"), nullable=False)
    # Fare amount for the trip
    trip_fare: mapped_column[Float] = mapped_column(Float, nullable=False)

    # Locations stored as JSON objects (latitude, longitude, and address)
    startlocation: mapped_column[dict] = mapped_column(JSON, nullable=True)  # Start location
    currentlocation: mapped_column[dict] = mapped_column(JSON, nullable=True)  # Current location during the ride
    endlocation: mapped_column[dict] = mapped_column(JSON, nullable=True)  # End location

    # Timestamps
    starts_at: mapped_column[datetime] = mapped_column(DateTime, nullable=False)  # Start time of the ride
    ends_at: mapped_column[datetime] = mapped_column(DateTime, nullable=True)  # End time of the ride

    created_at: mapped_column[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # Created timestamp (UTC)
    updated_at: mapped_column[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Updated timestamp (auto updates)

    # Luggage weights
    suitcase: mapped_column[Float] = mapped_column(Float, default=0.0, nullable=False, comment='0.02 per unit price for suitcase weight')
    handluggage: mapped_column[Float] = mapped_column(Float, default=0.0, nullable=False, comment='0.02 per unit price for hand luggage weight')
    otherluggage: mapped_column[Float] = mapped_column(Float, default=0.0, nullable=False, comment='0.02 per unit price for other luggage weight')

    __table_args__ = (
        CheckConstraint(suitcase >= 0, name="check_suitcase_weight_positive"),
        CheckConstraint(handluggage >= 0, name="check_handluggage_weight_positive"),
        CheckConstraint(otherluggage >= 0, name="check_otherluggage_weight_positive"),
    )

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

    def __repr__(self):
        return f"<Ride(id={self.id}, startlocation={self.startlocation}, endlocation={self.endlocation}, duration={self.duration}, status={self.status}, fare_amount={self.total_fare})>"