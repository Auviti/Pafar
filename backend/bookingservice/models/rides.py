from sqlalchemy import Integer, String, ForeignKey, Enum, DateTime, JSON, Float, CheckConstraint, Boolean, Text
from sqlalchemy.orm import mapped_column, Mapped, relationship, validates
from sqlalchemy.dialects.postgresql import TIMESTAMP

from core.database import Base, CHAR_LENGTH
from datetime import datetime
from enum import Enum as PyEnum
from uuid import UUID,uuid4
from typing import List, Optional
import sys



# Database type detection
if 'postgresql' in sys.argv:
    # Use native UUID for PostgreSQL
    UUIDType = UUID(as_uuid=True)
    mappeditem = UUID
    default = uuid4
else:
    # Use string representation for other databases
    UUIDType = String(36)
    mappeditem = str
    default = lambda: str(uuid4())
# Enum for Ride Status
class RideStatus(PyEnum):
    UPCOMING = "UPCOMING"
    ASSIGNED = "ASSIGNED"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"
class RideClass(PyEnum):
    ECONOMY = "ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST_CLASS = "FIRST_CLASS"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"

class RideType(PyEnum):
    ROUND = "ROUND"
    ONE_WAY = "ONE_WAY"
    MULTICITY = "MULTICITY"

# Ride Model
class Ride(Base):
    __tablename__ = "rides"

    # Ride ID (UUID as the primary key)
    id: Mapped[UUID] = mapped_column(UUIDType, primary_key=True, default=default)  # UUID with auto-generation
    name: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)
    # Ride Status (Assigned, Ongoing, Completed, Canceled)
    status: Mapped[RideStatus] = mapped_column(Enum(RideStatus), nullable=False)
    ride_class: Mapped[RideClass] = mapped_column(Enum(RideClass), default=RideClass.ECONOMY)  # Class of the trip (Economy, Business, etc.)
    ride_type: Mapped[RideClass] = mapped_column(Enum(RideType), default=RideType.ONE_WAY)
    
    # Foreign key referencing the Vehicle table (UUID)
    vehicle_id: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False) 

    # Fare amount for the trip
    trip_fare: Mapped[Float] = mapped_column(Float, nullable=False)

    # Locations stored as JSON objects (latitude, longitude, and address)
    startlocation: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)
    currentlocation: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)
    endlocation: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)

    # Timestamps
    starts_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)  # Start time of the ride
    ends_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)  # End time of the ride

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)  # Created timestamp (UTC)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)  # Updated timestamp (auto updates)

    # Luggage weights
    suitcase: Mapped[Float] = mapped_column(Float, default=0.0, nullable=False, comment='0.02 per unit price for suitcase weight')
    handluggage: Mapped[Float] = mapped_column(Float, default=0.0, nullable=False, comment='0.02 per unit price for hand luggage weight')
    otherluggage: Mapped[Float] = mapped_column(Float, default=0.0, nullable=False, comment='0.02 per unit price for other luggage weight')

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

    def to_dict(self):
        """Convert the Ride object to a dictionary"""
        return {
            "id": str(self.id),  # Convert UUID to string
            "name": self.name,
            "status": self.status.value,
            "ride_class": self.ride_class.value,
            "ride_type":self.ride_type.value,
            "vehicle_id": str(self.vehicle_id),
            "trip_fare": self.trip_fare,
            "startlocation": self.startlocation,
            "currentlocation": self.currentlocation,
            "endlocation": self.endlocation,
            "starts_at": self.starts_at.isoformat() if self.starts_at else None,
            "ends_at": self.ends_at.isoformat() if self.ends_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "suitcase": self.suitcase,
            "handluggage": self.handluggage,
            "otherluggage": self.otherluggage,
            "duration": self.duration,
            "total_fare": self.total_fare
        }
    